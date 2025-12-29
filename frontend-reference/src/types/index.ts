export type Role = 'PILOT' | 'TECHNICIAN' | 'COMMANDER' | 'ADMIN' | 'TRAINEE' | 'EMERGENCY' | 'FAMILY' | 'OPS_OFFICER';

export type AircraftStatus = 'READY' | 'IN_MAINTENANCE' | 'GROUNDED' | 'IN_FLIGHT';

export type MaintenanceStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export type EmergencyStatus = 'ACTIVE' | 'RESOLVING' | 'COMPLETED';

export type EmergencyType = 'FIRE' | 'RUNWAY_INCURSION' | 'AIRCRAFT_EMERGENCY' | 'MEDICAL' | 'SECURITY' | 'WEATHER' | 'OTHER';

export type MissionStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export type MissionType = 'TRAINING' | 'PATROL' | 'TRANSPORT' | 'MAINTENANCE_FERRY' | 'SEARCH_AND_RESCUE' | 'OTHER';

export type RunwayStatus = 'OPEN' | 'CAUTION' | 'CLOSED' | 'UNKNOWN';

export interface User {
    id: string;
    email: string;
    username: string;
    firstName: string;
    lastName: string;
    role: Role;
    isActive: boolean;
}

export interface Aircraft {
    id: string;
    tailNumber: string;
    type: string;
    model: string;
    squadron?: string;
    status: AircraftStatus;
    location?: string;
    fuelLevel?: number;
    flightHours: number;
    lastMaintenance?: string;
    nextMaintenance?: string;
}

export interface MaintenanceLog {
    id: string;
    aircraftId: string;
    technicianId: string;
    taskType: string;
    description: string;
    status: MaintenanceStatus;
    priority?: string;
    startedAt?: string;
    completedAt?: string;
    dueDate?: string;
    notes?: string;
    aircraft?: Aircraft;
    technician?: User;
    createdAt?: string;
}

export interface Emergency {
    id: string;
    type: EmergencyType;
    title: string;
    description: string;
    location: string;
    status: EmergencyStatus;
    severity: string;
    createdAt: string;
    updatedAt: string;
    resolvedAt?: string;
}

export interface Notification {
    id: string;
    userId: string;
    title: string;
    message: string;
    type: 'INFO' | 'WARNING' | 'EMERGENCY' | 'SUCCESS';
    isRead: boolean;
    createdAt: string;
}

export interface Mission {
    id: string;
    title: string;
    description?: string;
    aircraftId?: string;
    pilotId?: string;
    startTime: string;
    endTime?: string;
    status: MissionStatus;
    type: MissionType;
    originLat?: number;
    originLon?: number;
    originName?: string;
    destinationLat?: number;
    destinationLon?: number;
    destinationName?: string;
    createdAt: string;
    updatedAt: string;
    aircraft?: Aircraft;
    pilot?: User;
}

export interface WeatherSnapshot {
    id: string;
    locationName?: string;
    timestamp: string;
    temperature: number;
    condition: string;
    windSpeed: number;
    windDirection?: number;
    windGust?: number;
    visibility?: number;
    humidity?: number;
    pressure?: number;
    ceiling?: number;
    precipitation?: string;
    precipIntensity?: number;
    severeWeather?: string[];
    isStale?: boolean;
    staleSince?: string;
    statusReason?: string;
    rawJson?: string;
    runwayStatus?: RunwayStatus;
    runwayStatusReason?: string;
    runwayStatusFactors?: string[];
    isOverride?: boolean;
    overrideBy?: string;
    overrideExpiry?: string;
    formattedWeather?: string;
}

export interface FleetStats {
    READY: number;
    IN_MAINTENANCE: number;
    GROUNDED: number;
    IN_FLIGHT: number;
    total: number;
}

export interface PilotDashboardData {
    missions: Mission[];
    nextMission: Mission | null;
    assignedAircraft: Aircraft | null;
    fleetStats: FleetStats;
    recentMaintenance: MaintenanceLog[];
    weather: WeatherSnapshot | null;
    destinationWeather?: WeatherSnapshot | null;
    pilot?: {
        id: string;
        name: string;
        email: string;
    };
    alerts: Notification[];
    activeEmergencies: Emergency[];
    runwayStatus: RunwayStatus | string;
}

export interface AlertsData {
    notifications: Notification[];
    emergencies: Emergency[];
    total: number;
}

