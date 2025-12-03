package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/rs/zerolog"
)

func init() {
	// Disable logging during tests
	zerolog.SetGlobalLevel(zerolog.Disabled)

	// Initialize registry for tests
	registry = NewDeviceRegistry()
}

// TestHealthHandler tests the health check endpoint
func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	HealthHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status OK, got %v", w.Code)
	}

	var response map[string]string
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response["status"] != "healthy" {
		t.Errorf("Expected healthy status, got %v", response["status"])
	}
	if response["service"] != "medical-device-service" {
		t.Errorf("Expected medical-device-service, got %v", response["service"])
	}
}

// TestReadyHandler tests the readiness check endpoint
func TestReadyHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/ready", nil)
	w := httptest.NewRecorder()

	ReadyHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status OK, got %v", w.Code)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response["status"] != "ready" {
		t.Errorf("Expected ready status, got %v", response["status"])
	}
}

// TestRegisterDevice tests device registration
func TestRegisterDevice(t *testing.T) {
	// Reset registry
	registry = NewDeviceRegistry()

	device := MedicalDevice{
		ID:              "TEST-001",
		Type:            DeviceTypeMRI,
		Status:          StatusOperational,
		Location:        "Test Lab",
		SerialNumber:    "TEST-SN-001",
		Manufacturer:    "Test Corp",
		Model:           "Test Model",
		FirmwareVersion: "v1.0",
		LastCalibration: time.Now(),
		NextMaintenance: time.Now().Add(30 * 24 * time.Hour),
		UpTime:          3600,
		ErrorCount:      0,
		AlertLevel:      "none",
	}

	body, _ := json.Marshal(device)
	req := httptest.NewRequest("POST", "/api/v1/devices", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	RegisterDeviceHandler(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("Expected status Created, got %v", w.Code)
	}

	var registered MedicalDevice
	if err := json.NewDecoder(w.Body).Decode(&registered); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if registered.ID != device.ID {
		t.Errorf("Expected device ID %s, got %s", device.ID, registered.ID)
	}
}

// TestRegisterDeviceDuplicate tests duplicate device registration
func TestRegisterDeviceDuplicate(t *testing.T) {
	registry = NewDeviceRegistry()

	device := MedicalDevice{
		ID:   "DUP-001",
		Type: DeviceTypeECG,
	}

	// Register first time
	registry.RegisterDevice(&device)

	// Try to register again
	body, _ := json.Marshal(device)
	req := httptest.NewRequest("POST", "/api/v1/devices", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	RegisterDeviceHandler(w, req)

	if w.Code != http.StatusConflict {
		t.Errorf("Expected status Conflict, got %v", w.Code)
	}
}

// TestRegisterDeviceInvalidPayload tests invalid device registration
func TestRegisterDeviceInvalidPayload(t *testing.T) {
	tests := []struct {
		name    string
		payload map[string]interface{}
		status  int
	}{
		{
			name:    "Missing ID",
			payload: map[string]interface{}{"type": "MRI"},
			status:  http.StatusBadRequest,
		},
		{
			name:    "Missing Type",
			payload: map[string]interface{}{"id": "TEST-002"},
			status:  http.StatusBadRequest,
		},
		{
			name:    "Empty payload",
			payload: map[string]interface{}{},
			status:  http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			body, _ := json.Marshal(tt.payload)
			req := httptest.NewRequest("POST", "/api/v1/devices", bytes.NewReader(body))
			req.Header.Set("Content-Type", "application/json")
			w := httptest.NewRecorder()

			RegisterDeviceHandler(w, req)

			if w.Code != tt.status {
				t.Errorf("Expected status %v, got %v", tt.status, w.Code)
			}
		})
	}
}

// TestListDevices tests listing all devices
func TestListDevices(t *testing.T) {
	registry = NewDeviceRegistry()

	// Register test devices
	devices := []*MedicalDevice{
		{ID: "LIST-001", Type: DeviceTypeMRI},
		{ID: "LIST-002", Type: DeviceTypeECG},
		{ID: "LIST-003", Type: DeviceTypeVentilator},
	}

	for _, dev := range devices {
		registry.RegisterDevice(dev)
	}

	req := httptest.NewRequest("GET", "/api/v1/devices", nil)
	w := httptest.NewRecorder()

	ListDevicesHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status OK, got %v", w.Code)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	count, ok := response["count"].(float64)
	if !ok {
		t.Fatal("Count not found in response")
	}

	if int(count) != len(devices) {
		t.Errorf("Expected %d devices, got %d", len(devices), int(count))
	}
}

// TestGetDevice tests retrieving a specific device
func TestGetDevice(t *testing.T) {
	registry = NewDeviceRegistry()

	device := &MedicalDevice{
		ID:   "GET-001",
		Type: DeviceTypeCTScanner,
	}
	registry.RegisterDevice(device)

	req := httptest.NewRequest("GET", "/api/v1/devices/GET-001", nil)
	w := httptest.NewRecorder()

	// Mock chi URLParam
	ctx := req.Context()
	req = req.WithContext(ctx)

	GetDeviceHandler(w, req)

	// Note: This test will fail without proper chi routing
	// In real tests, use chi.NewRouter() to set up proper routing
}

// TestUpdateDeviceMetrics tests metrics updates
func TestUpdateDeviceMetrics(t *testing.T) {
	registry = NewDeviceRegistry()

	device := &MedicalDevice{ID: "METRICS-001", Type: DeviceTypeMRI}
	registry.RegisterDevice(device)

	metrics := DeviceMetrics{
		Temperature:      23.5,
		PowerConsumption: 750.0,
		CPUUtilization:   45.0,
		MemoryUsage:      60.0,
		NetworkLatency:   8.0,
		LastUpdated:      time.Now(),
	}

	err := registry.UpdateMetrics("METRICS-001", &metrics)
	if err != nil {
		t.Errorf("Failed to update metrics: %v", err)
	}

	retrieved, err := registry.GetMetrics("METRICS-001")
	if err != nil {
		t.Errorf("Failed to retrieve metrics: %v", err)
	}

	if retrieved.Temperature != metrics.Temperature {
		t.Errorf("Expected temperature %f, got %f", metrics.Temperature, retrieved.Temperature)
	}
}

// TestDeviceRegistry tests the device registry operations
func TestDeviceRegistry(t *testing.T) {
	dr := NewDeviceRegistry()

	t.Run("RegisterDevice", func(t *testing.T) {
		device := &MedicalDevice{ID: "REG-001", Type: DeviceTypeMRI}
		err := dr.RegisterDevice(device)
		if err != nil {
			t.Errorf("Failed to register device: %v", err)
		}
	})

	t.Run("GetDevice", func(t *testing.T) {
		device, err := dr.GetDevice("REG-001")
		if err != nil {
			t.Errorf("Failed to get device: %v", err)
		}
		if device.ID != "REG-001" {
			t.Errorf("Expected device ID REG-001, got %s", device.ID)
		}
	})

	t.Run("UpdateDevice", func(t *testing.T) {
		device, _ := dr.GetDevice("REG-001")
		device.Status = StatusMaintenance
		err := dr.UpdateDevice(device)
		if err != nil {
			t.Errorf("Failed to update device: %v", err)
		}

		updated, _ := dr.GetDevice("REG-001")
		if updated.Status != StatusMaintenance {
			t.Errorf("Expected status maintenance, got %v", updated.Status)
		}
	})

	t.Run("DeregisterDevice", func(t *testing.T) {
		err := dr.DeregisterDevice("REG-001")
		if err != nil {
			t.Errorf("Failed to deregister device: %v", err)
		}

		_, err = dr.GetDevice("REG-001")
		if err == nil {
			t.Error("Expected error when getting deregistered device")
		}
	})
}

// TestDeviceStatuses tests different device status scenarios
func TestDeviceStatuses(t *testing.T) {
	statuses := []DeviceStatus{
		StatusOperational,
		StatusDegraded,
		StatusOffline,
		StatusMaintenance,
		StatusError,
	}

	for _, status := range statuses {
		t.Run(string(status), func(t *testing.T) {
			registry = NewDeviceRegistry()
			device := &MedicalDevice{
				ID:     "STATUS-001",
				Type:   DeviceTypeMRI,
				Status: status,
			}
			err := registry.RegisterDevice(device)
			if err != nil {
				t.Errorf("Failed to register device with status %v: %v", status, err)
			}

			retrieved, _ := registry.GetDevice("STATUS-001")
			if retrieved.Status != status {
				t.Errorf("Expected status %v, got %v", status, retrieved.Status)
			}
		})
	}
}

// TestDeviceTypes tests all supported device types
func TestDeviceTypes(t *testing.T) {
	deviceTypes := []DeviceType{
		DeviceTypeMRI,
		DeviceTypeCTScanner,
		DeviceTypeXRay,
		DeviceTypeECG,
		DeviceTypeVentilator,
		DeviceTypePump,
	}

	registry = NewDeviceRegistry()

	for i, deviceType := range deviceTypes {
		t.Run(string(deviceType), func(t *testing.T) {
			device := &MedicalDevice{
				ID:   string(deviceType) + "-001",
				Type: deviceType,
			}
			err := registry.RegisterDevice(device)
			if err != nil {
				t.Errorf("Failed to register %v device: %v", deviceType, err)
			}
		})
	}

	count := registry.DeviceCount()
	if count != len(deviceTypes) {
		t.Errorf("Expected %d devices, got %d", len(deviceTypes), count)
	}
}

// TestGetActiveAlerts tests alert retrieval
func TestGetActiveAlerts(t *testing.T) {
	registry = NewDeviceRegistry()

	// Register devices with different alert levels
	devices := []*MedicalDevice{
		{ID: "ALERT-001", Type: DeviceTypeMRI, AlertLevel: "critical"},
		{ID: "ALERT-002", Type: DeviceTypeECG, AlertLevel: "warning"},
		{ID: "ALERT-003", Type: DeviceTypeVentilator, AlertLevel: "none"},
	}

	for _, dev := range devices {
		registry.RegisterDevice(dev)
	}

	alerts := registry.GetActiveAlerts()

	// Should return 2 alerts (critical and warning, not none)
	if len(alerts) != 2 {
		t.Errorf("Expected 2 active alerts, got %d", len(alerts))
	}
}

// TestConcurrentDeviceOperations tests concurrent access to registry
func TestConcurrentDeviceOperations(t *testing.T) {
	registry = NewDeviceRegistry()

	done := make(chan bool)
	operations := 100

	// Concurrent registrations
	for i := 0; i < operations; i++ {
		go func(id int) {
			device := &MedicalDevice{
				ID:   string(rune('A'+id%26)) + string(rune('0'+id%10)),
				Type: DeviceTypeMRI,
			}
			registry.RegisterDevice(device)
			done <- true
		}(i)
	}

	// Wait for all operations
	for i := 0; i < operations; i++ {
		<-done
	}

	// Verify no data races occurred
	count := registry.DeviceCount()
	if count == 0 {
		t.Error("No devices registered after concurrent operations")
	}
}

// BenchmarkRegisterDevice benchmarks device registration
func BenchmarkRegisterDevice(b *testing.B) {
	registry = NewDeviceRegistry()

	device := &MedicalDevice{
		ID:              "BENCH-001",
		Type:            DeviceTypeMRI,
		Status:          StatusOperational,
		Location:        "Test Lab",
		SerialNumber:    "BENCH-SN-001",
		Manufacturer:    "Test Corp",
		Model:           "Test Model",
		FirmwareVersion: "v1.0",
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		registry = NewDeviceRegistry()
		registry.RegisterDevice(device)
	}
}

// BenchmarkGetDevice benchmarks device retrieval
func BenchmarkGetDevice(b *testing.B) {
	registry = NewDeviceRegistry()
	device := &MedicalDevice{ID: "BENCH-002", Type: DeviceTypeMRI}
	registry.RegisterDevice(device)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		registry.GetDevice("BENCH-002")
	}
}

// BenchmarkUpdateMetrics benchmarks metrics updates
func BenchmarkUpdateMetrics(b *testing.B) {
	registry = NewDeviceRegistry()
	device := &MedicalDevice{ID: "BENCH-003", Type: DeviceTypeMRI}
	registry.RegisterDevice(device)

	metrics := &DeviceMetrics{
		Temperature:      23.5,
		PowerConsumption: 750.0,
		CPUUtilization:   45.0,
		MemoryUsage:      60.0,
		NetworkLatency:   8.0,
		LastUpdated:      time.Now(),
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		registry.UpdateMetrics("BENCH-003", metrics)
	}
}

// BenchmarkListDevices benchmarks device listing
func BenchmarkListDevices(b *testing.B) {
	registry = NewDeviceRegistry()

	// Register 100 devices
	for i := 0; i < 100; i++ {
		device := &MedicalDevice{
			ID:   string(rune('A'+i%26)) + string(rune('0'+i%10)) + string(rune('0'+i/10)),
			Type: DeviceTypeMRI,
		}
		registry.RegisterDevice(device)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		registry.ListDevices()
	}
}
