package main

// RecordEncryptionOp records encryption operation metrics (stub for lightweight deployment)
func RecordEncryptionOp(operation string, status string, duration float64, dataSize int) {
	// Metrics disabled for lightweight deployment
}

// IncActiveRequests increments active requests counter (stub)
func IncActiveRequests() {
	// Metrics disabled for lightweight deployment
}

// DecActiveRequests decrements active requests counter (stub)
func DecActiveRequests() {
	// Metrics disabled for lightweight deployment
}

// RecordHTTPRequest records HTTP request metrics (stub)
func RecordHTTPRequest(method, path string, statusCode int, duration float64) {
	// Metrics disabled for lightweight deployment
}
