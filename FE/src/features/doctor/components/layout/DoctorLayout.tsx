// src/features/doctor/components/layout/DoctorLayout.tsx
import { useRef, type ReactNode } from "react";
import { Layout, Model, TabNode, type IJsonModel } from "flexlayout-react";
import "flexlayout-react/style/light.css";

interface DoctorLayoutProps {
    panels: {
        [key: string]: ReactNode;
    };
}

export default function DoctorLayout({ panels }: DoctorLayoutProps) {
    // 레이아웃 모델 정의
    const json: IJsonModel = {
        global: {
            tabEnableClose: false,
            tabEnableRename: false,
            tabEnableDrag: false,
            tabSetMinWidth: 200,
            tabSetMinHeight: 120,
            splitterSize: 6,
            splitterExtra: 4,
        },
        borders: [],
        layout: {
            type: "row", // 전체 가로 배치
            weight: 100,
            children: [
                // 1. 좌측 컬럼 (대기열 + 환자정보 + 세션목록) — 세로 리사이즈 가능
                {
                    type: "row",
                    weight: 25,
                    children: [
                        {
                            type: "tabset",
                            weight: 34,
                            children: [
                                { type: "tab", name: "환자 대기열", component: "waiting-list" }
                            ]
                        },
                        {
                            type: "tabset",
                            weight: 33,
                            children: [
                                { type: "tab", name: "환자 정보", component: "patient-detail" }
                            ]
                        },
                        {
                            type: "tabset",
                            weight: 33,
                            children: [
                                { type: "tab", name: "영상 목록", component: "session-list" }
                            ]
                        }
                    ]
                },
                // 2. 중앙 영상 분석
                {
                    type: "tabset",
                    weight: 40,
                    children: [
                        { type: "tab", name: "영상 분석", component: "central-analysis" }
                    ]
                },
                // 3. 우측 컬럼 (트렌드 + AI 진단) — 세로 리사이즈 가능
                {
                    type: "row",
                    weight: 35,
                    children: [
                        {
                            type: "tabset",
                            weight: 50,
                            children: [
                                { type: "tab", name: "지표 변화", component: "trend-chart" }
                            ]
                        },
                        {
                            type: "tabset",
                            weight: 50,
                            children: [
                                { type: "tab", name: "AI 진단", component: "ai-diagnosis" }
                            ]
                        }
                    ]
                }
            ]
        }
    };

    const modelRef = useRef(Model.fromJson(json));

    // 패널 렌더링 팩토리
    const factory = (node: TabNode) => {
        const component = node.getComponent();
        if (component && panels[component]) {
            return (
                <div className="h-full w-full overflow-hidden flex flex-col">
                    {panels[component]}
                </div>
            );
        }
        return <div>Unknown component: {component}</div>;
    };

    return (
        <div className="w-full h-full relative">
            {/* Windows 98 스타일 오버라이드 */}
            <style>{`
                .flexlayout__layout {
                    background: #808080 !important;
                }
                .flexlayout__tabset {
                    background: #d4d0c8 !important;
                    border: 2px solid;
                    border-color: white #808080 #808080 white !important;
                }
                .flexlayout__tabset_header {
                    background: #000080 !important;
                }
                .flexlayout__tab_button {
                    font-family: 'Gulim', sans-serif !important;
                    font-size: 11px !important;
                    font-weight: bold !important;
                    color: #000080 !important;
                    background: #d4d0c8 !important;
                    border: 1px solid;
                    border-color: white #808080 #808080 white !important;
                    padding: 2px 8px !important;
                }
                .flexlayout__tab_button--selected {
                    background: #f0f0f0 !important;
                }
                .flexlayout__tab_button:hover {
                    background: #e0e0e0 !important;
                }
                .flexlayout__tab {
                    background: white !important;
                    border: 1px solid #808080 !important;
                }
                .flexlayout__splitter {
                    background: #808080 !important;
                    border: 1px solid;
                    border-color: #c0c0c0 #404040 #404040 #c0c0c0 !important;
                }
                .flexlayout__splitter:hover {
                    background: #a0a0a0 !important;
                }
                .flexlayout__splitter_drag {
                    background: #000080 !important;
                    opacity: 0.5 !important;
                }
            `}</style>

            <Layout
                model={modelRef.current}
                factory={factory}
            />
        </div>
    );
}