import mockTelemetry from "./mockTelemetry.json";

const STATUS_LABELS = {
  distress: "Distress",
  moving: "Moving",
  idle: "Idle",
  unknown: "Unknown",
};

export function getInitialTelemetry() {
  return mockTelemetry.map((item) => ({ ...item }));
}

export function getStatusLabel(flags) {
  if (flags & 4) return STATUS_LABELS.distress;
  if (flags & 2) return STATUS_LABELS.moving;
  if (flags & 1) return STATUS_LABELS.idle;
  return STATUS_LABELS.unknown;
}

export function getStatusColor(flags) {
  if (flags & 4) return "#f87171";
  if (flags & 2) return "#fbbf24";
  if (flags & 1) return "#34d399";
  return "#9ca3af";
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function randomDelta(scale = 0.0005) {
  return (Math.random() - 0.5) * scale;
}

export function simulateTelemetryStep(data) {
  const now = new Date();

  return data.map((item) => {
    const nextBattery = clamp(item.battery - Math.random() * 1.5, 0, 100);
    const nextFlags = computeNextFlags(item.flags, nextBattery);
    const nextLat = parseFloat((item.latitude + randomDelta()).toFixed(5));
    const nextLon = parseFloat((item.longitude + randomDelta()).toFixed(5));
    const nextTimestamp = new Date(now.getTime() + 1000).toISOString();

    return {
      ...item,
      latitude: nextLat,
      longitude: nextLon,
      battery: Math.round(nextBattery),
      flags: nextFlags,
      timestamp: nextTimestamp,
    };
  });
}

function computeNextFlags(currentFlags, battery) {
  let nextFlags = currentFlags;

  if (battery <= 20) {
    nextFlags |= 4; // distress
  } else {
    nextFlags &= ~4;
  }

  if (Math.random() < 0.2) {
    nextFlags = nextFlags ^ 2; // toggle moving bit
  }

  if (!(nextFlags & 2) && !(nextFlags & 4)) {
    nextFlags |= 1; // idle fallback
  } else {
    nextFlags &= ~1;
  }

  return nextFlags;
}
