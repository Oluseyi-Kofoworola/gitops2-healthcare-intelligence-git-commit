package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/trace"
)

// DeviceStatus represents the operational status of a medical device
type DeviceStatus string

const (
	StatusOperational DeviceStatus = "operational"
	StatusDegraded    DeviceStatus = "degraded"
	StatusOffline     DeviceStatus = "offline"
	StatusMaintenance DeviceStatus = "maintenance"
	StatusError       DeviceStatus = "error"
)

// DeviceType represents the type of medical device
type DeviceType string

const (
	DeviceTypeMRI        DeviceType = "MRI"
	DeviceTypeCTScanner  DeviceType = "CT_Scanner"
	DeviceTypeXRay       DeviceType = "X-Ray"
	DeviceTypeECG        DeviceType = "ECG"
	DeviceTypeVentilator DeviceType = "Ventilator"
	DeviceTypePump       DeviceType = "Infusion_Pump"
)

// MedicalDevice represents a monitored medical device
type MedicalDevice struct {
	ID              string       `json:"id"`
	Type            DeviceType   `json:"type"`
	Status          DeviceStatus `json:"status"`
	Location        string       `json:"location"`
	SerialNumber    string       `json:"serial_number"`
	Manufacturer    string       `json:"manufacturer"`
	Model           string       `json:"model"`
	FirmwareVersion string       `json:"firmware_version"`
	LastCalibration time.Time    `json:"last_calibration"`
	NextMaintenance time.Time    `json:"next_maintenance"`
	UpTime          int64        `json:"uptime_seconds"`
	ErrorCount      int          `json:"error_count"`
	AlertLevel      string       `json:"alert_level"`
	mu              sync.RWMutex
}

// DeviceMetrics represents operational metrics for a device
type DeviceMetrics struct {
	Temperature      float64   `json:"temperature_celsius"`
	PowerConsumption float64   `json:"power_consumption_watts"`
	CPUUtilization   float64   `json:"cpu_utilization_percent"`
	MemoryUsage      float64   `json:"memory_usage_percent"`
	NetworkLatency   float64   `json:"network_latency_ms"`
	LastUpdated      time.Time `json:"last_updated"`
}

// DeviceRegistry manages all registered medical devices
type DeviceRegistry struct {
	devices map[string]*MedicalDevice
	metrics map[string]*DeviceMetrics
	mu      sync.RWMutex
}

var (
	registry *DeviceRegistry
)

func main() {
	// Initialize structured logging
	initLogging()

	log.Info().Msg("Starting Medical Device Monitoring Service...")

	// Load configuration
	port := getEnv("PORT", "8084")

	// Initialize device registry
	registry = NewDeviceRegistry()
	log.Info().Msg("Device registry initialized")

	// Initialize OpenTelemetry tracing (disabled for lightweight deployment)
	ctx := context.Background()
	if err := InitTracerProvider("medical-device-service"); err != nil {
		log.Warn().Err(err).Msg("Failed to initialize tracer provider, continuing without tracing")
	} else {
		defer func() {
			if err := ShutdownTracer(ctx); err != nil {
				log.Error().Err(err).Msg("Failed to shutdown tracer provider")
			}
		}()
		log.Info().Msg("OpenTelemetry tracing initialized (stub mode)")
	}
	_ = ctx // Mark as used

	// Setup HTTP router
	r := chi.NewRouter()

	// Middleware stack
	r.Use(middleware.Recoverer)
	r.Use(middleware.RealIP)
	r.Use(middleware.RequestID)
	r.Use(LoggingMiddleware)
	r.Use(TracingMiddleware)
	r.Use(PrometheusMiddleware)
	r.Use(CORSMiddleware)
	r.Use(middleware.Compress(5))
	r.Use(middleware.Timeout(30 * time.Second))

	// Health & readiness endpoints
	r.Get("/health", HealthHandler)
	r.Get("/ready", ReadyHandler)

	// Metrics endpoint
	r.Handle("/metrics", promhttp.Handler())

	// API routes
	r.Route("/api/v1", func(r chi.Router) {
		// Device management
		r.Post("/devices", RegisterDeviceHandler)
		r.Get("/devices", ListDevicesHandler)
		r.Get("/devices/{deviceID}", GetDeviceHandler)
		r.Put("/devices/{deviceID}", UpdateDeviceHandler)
		r.Delete("/devices/{deviceID}", DeregisterDeviceHandler)

		// Device metrics
		r.Get("/devices/{deviceID}/metrics", GetDeviceMetricsHandler)
		r.Post("/devices/{deviceID}/metrics", UpdateDeviceMetricsHandler)

		// Device operations
		r.Post("/devices/{deviceID}/calibrate", CalibrateDeviceHandler)
		r.Post("/devices/{deviceID}/maintenance", ScheduleMaintenanceHandler)
		r.Post("/devices/{deviceID}/diagnostics", RunDiagnosticsHandler)

		// Alerts and monitoring
		r.Get("/alerts", ListAlertsHandler)
		r.Get("/devices/{deviceID}/status", GetDeviceStatusHandler)
	})

	// Start HTTP server
	addr := ":" + port
	server := &http.Server{
		Addr:         addr,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Info().Str("address", addr).Msg("HTTP server starting")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal().Err(err).Msg("HTTP server failed")
		}
	}()

	// Start background device simulator for demo purposes
	if getEnv("ENABLE_SIMULATOR", "true") == "true" {
		go startDeviceSimulator()
	}

	// Wait for interrupt signal for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info().Msg("Shutting down server...")

	// Graceful shutdown with 30 second timeout
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Error().Err(err).Msg("Server forced to shutdown")
	}

	log.Info().Msg("Server shutdown complete")
}

// initLogging configures structured logging with zerolog
func initLogging() {
	if os.Getenv("ENV") == "development" {
		log.Logger = log.Output(zerolog.ConsoleWriter{Out: os.Stderr, TimeFormat: time.RFC3339})
	} else {
		zerolog.TimeFieldFormat = zerolog.TimeFormatUnix
	}

	logLevel := os.Getenv("LOG_LEVEL")
	switch logLevel {
	case "debug":
		zerolog.SetGlobalLevel(zerolog.DebugLevel)
	case "info":
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	case "warn":
		zerolog.SetGlobalLevel(zerolog.WarnLevel)
	case "error":
		zerolog.SetGlobalLevel(zerolog.ErrorLevel)
	default:
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
	}
}

// getEnv retrieves environment variable with default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

// NewDeviceRegistry creates a new device registry
func NewDeviceRegistry() *DeviceRegistry {
	return &DeviceRegistry{
		devices: make(map[string]*MedicalDevice),
		metrics: make(map[string]*DeviceMetrics),
	}
}

// HealthHandler handles health check endpoint
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "healthy",
		"service": "medical-device-service",
	})
}

// ReadyHandler handles readiness check endpoint
func ReadyHandler(w http.ResponseWriter, r *http.Request) {
	if registry == nil {
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{
			"status": "not ready",
			"reason": "device registry not initialized",
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":        "ready",
		"service":       "medical-device-service",
		"device_count":  registry.DeviceCount(),
		"active_alerts": registry.GetActiveAlertCount(),
	})
}

// RegisterDeviceHandler registers a new medical device
func RegisterDeviceHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var device MedicalDevice
	if err := json.NewDecoder(r.Body).Decode(&device); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordDeviceOperation("register", "error", time.Since(start).Seconds())
		return
	}

	// Validate device
	if device.ID == "" || device.Type == "" {
		http.Error(w, "Device ID and type are required", http.StatusBadRequest)
		RecordDeviceOperation("register", "error", time.Since(start).Seconds())
		span.SetAttributes(attribute.String("error.type", "validation"))
		return
	}

	// Register device
	if err := registry.RegisterDevice(&device); err != nil {
		log.Error().Err(err).Str("device_id", device.ID).Msg("Failed to register device")
		http.Error(w, err.Error(), http.StatusConflict)
		RecordDeviceOperation("register", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	// Record metrics
	duration := time.Since(start).Seconds()
	RecordDeviceOperation("register", "success", duration)
	span.SetAttributes(
		attribute.String("device.id", device.ID),
		attribute.String("device.type", string(device.Type)),
	)

	log.Info().Str("device_id", device.ID).Str("type", string(device.Type)).Msg("Device registered")

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(&device)
}

// ListDevicesHandler lists all registered devices
func ListDevicesHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	start := time.Now()

	devices := registry.ListDevices()

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("list", "success", duration)

	span := trace.SpanFromContext(ctx)
	span.SetAttributes(attribute.Int("device.count", len(devices)))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"devices": devices,
		"count":   len(devices),
	})
}

// GetDeviceHandler retrieves a specific device
func GetDeviceHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	device, err := registry.GetDevice(deviceID)
	if err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		RecordDeviceOperation("get", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("get", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(&device)
}

// UpdateDeviceHandler updates device information
func UpdateDeviceHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var updates MedicalDevice
	if err := json.NewDecoder(r.Body).Decode(&updates); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordDeviceOperation("update", "error", time.Since(start).Seconds())
		return
	}

	updates.ID = deviceID
	if err := registry.UpdateDevice(&updates); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		RecordDeviceOperation("update", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("update", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	log.Info().Str("device_id", deviceID).Msg("Device updated")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(&updates)
}

// DeregisterDeviceHandler removes a device from registry
func DeregisterDeviceHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	if err := registry.DeregisterDevice(deviceID); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		RecordDeviceOperation("deregister", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("deregister", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	log.Info().Str("device_id", deviceID).Msg("Device deregistered")

	w.WriteHeader(http.StatusNoContent)
}

// GetDeviceMetricsHandler retrieves device metrics
func GetDeviceMetricsHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	metrics, err := registry.GetMetrics(deviceID)
	if err != nil {
		http.Error(w, "Metrics not found", http.StatusNotFound)
		RecordDeviceOperation("get_metrics", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("get_metrics", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// UpdateDeviceMetricsHandler updates device metrics
func UpdateDeviceMetricsHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var metrics DeviceMetrics
	if err := json.NewDecoder(r.Body).Decode(&metrics); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordDeviceOperation("update_metrics", "error", time.Since(start).Seconds())
		return
	}

	metrics.LastUpdated = time.Now()
	if err := registry.UpdateMetrics(deviceID, &metrics); err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		RecordDeviceOperation("update_metrics", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("update_metrics", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(metrics)
}

// CalibrateDeviceHandler triggers device calibration
func CalibrateDeviceHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	device, err := registry.GetDevice(deviceID)
	if err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		RecordDeviceOperation("calibrate", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	// Simulate calibration
	device.mu.Lock()
	device.LastCalibration = time.Now()
	device.mu.Unlock()

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("calibrate", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	log.Info().Str("device_id", deviceID).Msg("Device calibrated")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"device_id":        deviceID,
		"last_calibration": device.LastCalibration,
		"status":           "calibration_complete",
	})
}

// ScheduleMaintenanceHandler schedules device maintenance
func ScheduleMaintenanceHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	var req struct {
		ScheduledTime time.Time `json:"scheduled_time"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		RecordDeviceOperation("schedule_maintenance", "error", time.Since(start).Seconds())
		return
	}

	device, err := registry.GetDevice(deviceID)
	if err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		RecordDeviceOperation("schedule_maintenance", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	device.mu.Lock()
	device.NextMaintenance = req.ScheduledTime
	device.mu.Unlock()

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("schedule_maintenance", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	log.Info().Str("device_id", deviceID).Time("scheduled", req.ScheduledTime).Msg("Maintenance scheduled")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"device_id":        deviceID,
		"next_maintenance": device.NextMaintenance,
		"status":           "maintenance_scheduled",
	})
}

// RunDiagnosticsHandler runs device diagnostics
func RunDiagnosticsHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	device, err := registry.GetDevice(deviceID)
	if err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		RecordDeviceOperation("diagnostics", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	// Simulate diagnostics
	results := map[string]interface{}{
		"device_id":    deviceID,
		"type":         device.Type,
		"status":       device.Status,
		"error_count":  device.ErrorCount,
		"uptime":       device.UpTime,
		"tests_run":    5,
		"tests_passed": 5,
		"tests_failed": 0,
		"timestamp":    time.Now(),
		"result":       "pass",
	}

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("diagnostics", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	log.Info().Str("device_id", deviceID).Msg("Diagnostics completed")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

// ListAlertsHandler lists active alerts
func ListAlertsHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	start := time.Now()

	alerts := registry.GetActiveAlerts()

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("list_alerts", "success", duration)

	span := trace.SpanFromContext(ctx)
	span.SetAttributes(attribute.Int("alert.count", len(alerts)))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"alerts": alerts,
		"count":  len(alerts),
	})
}

// GetDeviceStatusHandler retrieves device status
func GetDeviceStatusHandler(w http.ResponseWriter, r *http.Request) {
	deviceID := chi.URLParam(r, "deviceID")
	ctx := r.Context()
	span := trace.SpanFromContext(ctx)
	start := time.Now()

	device, err := registry.GetDevice(deviceID)
	if err != nil {
		http.Error(w, "Device not found", http.StatusNotFound)
		RecordDeviceOperation("get_status", "error", time.Since(start).Seconds())
		span.RecordError(err)
		return
	}

	duration := time.Since(start).Seconds()
	RecordDeviceOperation("get_status", "success", duration)
	span.SetAttributes(attribute.String("device.id", deviceID))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"device_id":   deviceID,
		"status":      device.Status,
		"alert_level": device.AlertLevel,
		"error_count": device.ErrorCount,
		"uptime":      device.UpTime,
		"timestamp":   time.Now(),
	})
}

// CORSMiddleware handles CORS headers
func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// startDeviceSimulator simulates device data for demo purposes
func startDeviceSimulator() {
	log.Info().Msg("Starting device simulator")

	// Register sample devices
	devices := []*MedicalDevice{
		{
			ID:              "MRI-001",
			Type:            DeviceTypeMRI,
			Status:          StatusOperational,
			Location:        "Radiology Department - Room 101",
			SerialNumber:    "MRI-2024-001",
			Manufacturer:    "Siemens Healthineers",
			Model:           "MAGNETOM Vida",
			FirmwareVersion: "VA30A",
			LastCalibration: time.Now().Add(-24 * time.Hour),
			NextMaintenance: time.Now().Add(30 * 24 * time.Hour),
			UpTime:          86400,
			ErrorCount:      0,
			AlertLevel:      "none",
		},
		{
			ID:              "ECG-002",
			Type:            DeviceTypeECG,
			Status:          StatusOperational,
			Location:        "Cardiology - ICU Floor 3",
			SerialNumber:    "ECG-2024-002",
			Manufacturer:    "GE Healthcare",
			Model:           "MAC 2000",
			FirmwareVersion: "v3.2.1",
			LastCalibration: time.Now().Add(-12 * time.Hour),
			NextMaintenance: time.Now().Add(15 * 24 * time.Hour),
			UpTime:          43200,
			ErrorCount:      0,
			AlertLevel:      "none",
		},
		{
			ID:              "VENT-003",
			Type:            DeviceTypeVentilator,
			Status:          StatusOperational,
			Location:        "ICU - Room 305",
			SerialNumber:    "VENT-2024-003",
			Manufacturer:    "Dräger",
			Model:           "Evita V800",
			FirmwareVersion: "v2.1.5",
			LastCalibration: time.Now().Add(-6 * time.Hour),
			NextMaintenance: time.Now().Add(7 * 24 * time.Hour),
			UpTime:          21600,
			ErrorCount:      0,
			AlertLevel:      "none",
		},
	}

	for _, device := range devices {
		if err := registry.RegisterDevice(device); err != nil {
			log.Error().Err(err).Str("device_id", device.ID).Msg("Failed to register sample device")
		} else {
			log.Info().Str("device_id", device.ID).Str("type", string(device.Type)).Msg("Sample device registered")

			// Initialize metrics
			metrics := &DeviceMetrics{
				Temperature:      22.0 + rand.Float64()*3.0,
				PowerConsumption: 500 + rand.Float64()*500,
				CPUUtilization:   30 + rand.Float64()*40,
				MemoryUsage:      40 + rand.Float64()*30,
				NetworkLatency:   5 + rand.Float64()*10,
				LastUpdated:      time.Now(),
			}
			registry.UpdateMetrics(device.ID, metrics)
		}
	}

	// Update metrics periodically
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		devices := registry.ListDevices()
		for _, device := range devices {
			metrics := &DeviceMetrics{
				Temperature:      22.0 + rand.Float64()*3.0,
				PowerConsumption: 500 + rand.Float64()*500,
				CPUUtilization:   30 + rand.Float64()*40,
				MemoryUsage:      40 + rand.Float64()*30,
				NetworkLatency:   5 + rand.Float64()*10,
				LastUpdated:      time.Now(),
			}
			registry.UpdateMetrics(device.ID, metrics)

			// Update uptime
			dev, _ := registry.GetDevice(device.ID)
			dev.mu.Lock()
			dev.UpTime += 10
			dev.mu.Unlock()
		}
	}
}

// DeviceRegistry methods

func (dr *DeviceRegistry) RegisterDevice(device *MedicalDevice) error {
	dr.mu.Lock()
	defer dr.mu.Unlock()

	if _, exists := dr.devices[device.ID]; exists {
		return fmt.Errorf("device %s already registered", device.ID)
	}

	dr.devices[device.ID] = device
	return nil
}

func (dr *DeviceRegistry) GetDevice(deviceID string) (*MedicalDevice, error) {
	dr.mu.RLock()
	defer dr.mu.RUnlock()

	device, exists := dr.devices[deviceID]
	if !exists {
		return nil, fmt.Errorf("device %s not found", deviceID)
	}

	return device, nil
}

func (dr *DeviceRegistry) UpdateDevice(device *MedicalDevice) error {
	dr.mu.Lock()
	defer dr.mu.Unlock()

	if _, exists := dr.devices[device.ID]; !exists {
		return fmt.Errorf("device %s not found", device.ID)
	}

	dr.devices[device.ID] = device
	return nil
}

func (dr *DeviceRegistry) DeregisterDevice(deviceID string) error {
	dr.mu.Lock()
	defer dr.mu.Unlock()

	if _, exists := dr.devices[deviceID]; !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	delete(dr.devices, deviceID)
	delete(dr.metrics, deviceID)
	return nil
}

func (dr *DeviceRegistry) ListDevices() []*MedicalDevice {
	dr.mu.RLock()
	defer dr.mu.RUnlock()

	devices := make([]*MedicalDevice, 0, len(dr.devices))
	for _, device := range dr.devices {
		devices = append(devices, device)
	}

	return devices
}

func (dr *DeviceRegistry) DeviceCount() int {
	dr.mu.RLock()
	defer dr.mu.RUnlock()
	return len(dr.devices)
}

func (dr *DeviceRegistry) UpdateMetrics(deviceID string, metrics *DeviceMetrics) error {
	dr.mu.Lock()
	defer dr.mu.Unlock()

	if _, exists := dr.devices[deviceID]; !exists {
		return fmt.Errorf("device %s not found", deviceID)
	}

	dr.metrics[deviceID] = metrics
	return nil
}

func (dr *DeviceRegistry) GetMetrics(deviceID string) (*DeviceMetrics, error) {
	dr.mu.RLock()
	defer dr.mu.RUnlock()

	metrics, exists := dr.metrics[deviceID]
	if !exists {
		return nil, fmt.Errorf("metrics for device %s not found", deviceID)
	}

	return metrics, nil
}

func (dr *DeviceRegistry) GetActiveAlerts() []map[string]interface{} {
	dr.mu.RLock()
	defer dr.mu.RUnlock()

	alerts := make([]map[string]interface{}, 0)
	for _, device := range dr.devices {
		if device.AlertLevel != "none" && device.AlertLevel != "" {
			alerts = append(alerts, map[string]interface{}{
				"device_id":   device.ID,
				"device_type": device.Type,
				"alert_level": device.AlertLevel,
				"status":      device.Status,
				"location":    device.Location,
				"error_count": device.ErrorCount,
			})
		}
	}

	return alerts
}

func (dr *DeviceRegistry) GetActiveAlertCount() int {
	return len(dr.GetActiveAlerts())
}
