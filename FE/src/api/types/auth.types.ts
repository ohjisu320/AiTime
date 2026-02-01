// 사용자 로그인 응답 타입
export interface ApiResponseUserLogin {
    code: number;
    message: string;
    data: {
        accessToken: string;
        refreshToken?: string;
        userInfoDTO: {
            userId: number;
            name: string;
            userRole: string;
        };
    };
}

// 병원 관계자 로그인 응답 타입
export interface ApiResponseHospitalStaffLogin {
    code: number;
    message: string;
    data: {
        accessToken: string;
        refreshToken?: string;
        hospitalStaffInfoDTO: {
            hospitalStaffId: number;
            name: string;
            staffRole: 'DOCTOR' | 'DESK';
        };
    };
}
