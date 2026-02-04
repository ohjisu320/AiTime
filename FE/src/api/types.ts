export interface ApiResponse<T = any> {
    code: number;
    status: string;
    message: string;
    data: T;
}

export interface ApiError {
    code: number;
    message: string;
    status?: string;
}

export const StaffRole = {
    DOCTOR: 'DOCTOR',
    DESK: 'DESK',
} as const;

export type StaffRole = typeof StaffRole[keyof typeof StaffRole];
