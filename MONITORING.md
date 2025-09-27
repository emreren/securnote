# SecurNote Monitoring with Grafana + Prometheus

## 🔥 Professional monitoring stack for SecurNote

### Quick Start

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards
echo "Grafana: http://localhost:3000 (admin:securnote123)"
echo "Prometheus: http://localhost:9091"
echo "SecurNote Admin API: http://localhost:8000"
echo "SecurNote Metrics: http://localhost:9090/metrics"
```

## 📊 Monitoring Components

### 1. **Prometheus Metrics** (Port 9090)
- User operation counters
- Operation duration histograms
- Active user gauge
- Failed operation counters
- Notes creation metrics

### 2. **Grafana Dashboards** (Port 3000)
- **Default Login**: `admin` / `securnote123`
- Real-time user activity visualization
- Operation performance monitoring
- Error rate tracking
- User engagement analytics

### 3. **Admin API** (Port 8000)
- Basic auth: `admin` / `securnote123`
- Activity logs and statistics
- User operation history

## 📈 Available Metrics

```prometheus
# User operations by type and status
securnote_user_operations_total{username="user", operation="login", status="success"}

# Operation performance
securnote_operation_duration_seconds{operation="add_note"}

# System health
securnote_active_users
securnote_notes_total{username="user"}
securnote_failed_operations_total{operation="login", error_type="invalid_credentials"}
```

## 🎯 Key Dashboards

1. **User Operations Rate** - Real-time operation frequency
2. **Active Users** - Current active user count
3. **Operations by Type** - Distribution of operation types
4. **Failed Operations** - Error tracking and analysis
5. **Notes Created Over Time** - User engagement trends
6. **Operation Duration** - Performance monitoring

## 🔧 Configuration

### Environment Variables
```bash
METRICS_PORT=9090           # Prometheus metrics port
ADMIN_USERNAME=admin        # Admin API username
ADMIN_PASSWORD=securnote123 # Admin API password
LOG_LEVEL=INFO             # Logging level
```

### Custom Dashboards
Place custom dashboard JSON files in `grafana/dashboards/`

### Prometheus Rules
Add alerting rules in `prometheus/` directory

## 🚀 Production Deployment

For production use:
1. Change default passwords
2. Setup HTTPS with reverse proxy
3. Configure persistent storage
4. Add alerting rules
5. Setup log rotation

## 📋 Monitoring Checklist

- [x] Prometheus metrics collection
- [x] Grafana visualization
- [x] User activity tracking
- [x] Error monitoring
- [x] Performance metrics
- [x] Admin dashboard
- [ ] Alerting rules (optional)
- [ ] Log aggregation (optional)

## 🔍 Troubleshooting

```bash
# Check metrics endpoint
curl http://localhost:9090/metrics

# Check Prometheus targets
curl http://localhost:9091/api/v1/targets

# View container logs
docker-compose -f docker-compose.monitoring.yml logs grafana
docker-compose -f docker-compose.monitoring.yml logs prometheus
```