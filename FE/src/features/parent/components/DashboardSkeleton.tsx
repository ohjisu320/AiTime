// Loading Skeleton Components for Dashboard

export const HeroBannerSkeleton = () => (
    <div className="relative w-full h-[500px] md:h-[400px] lg:h-[350px] xl:h-80 bg-gradient-to-r from-gray-200 to-gray-300 rounded-3xl shadow-2xl overflow-hidden animate-pulse">
        <div className="p-16 flex items-center gap-12">
            {/* Icon skeleton */}
            <div className="w-32 h-32 bg-gray-300 rounded-full" />

            {/* Text skeleton */}
            <div className="flex flex-col gap-4 flex-1">
                <div className="h-12 bg-gray-300 rounded-lg w-3/4" />
                <div className="h-6 bg-gray-300 rounded-lg w-1/2" />
                <div className="h-10 bg-gray-300 rounded-full w-32 mt-2" />
            </div>
        </div>
    </div>
);

export const GuideVideoSkeleton = () => (
    <div className="relative w-full min-h-[450px] bg-gray-200 rounded-3xl shadow-xl overflow-hidden animate-pulse">
        <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 bg-gray-300 rounded-full" />
        </div>
    </div>
);

export const HospitalTimelineSkeleton = () => (
    <div className="w-full bg-white rounded-3xl shadow-xl p-6 border border-gray-100">
        <div className="flex items-center gap-3 mb-6">
            <div className="w-6 h-6 bg-gray-200 rounded animate-pulse" />
            <div className="h-6 bg-gray-200 rounded w-32 animate-pulse" />
        </div>

        <div className="flex flex-col items-center justify-center py-12 gap-4">
            <div className="w-16 h-16 bg-gray-200 rounded-full animate-pulse" />
            <div className="h-4 bg-gray-200 rounded w-48 animate-pulse" />
            <div className="h-3 bg-gray-200 rounded w-64 animate-pulse" />
            <div className="h-10 bg-gray-200 rounded-lg w-32 mt-4 animate-pulse" />
        </div>
    </div>
);

export const DashboardSkeleton = () => (
    <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-8 justify-center">
        <div className="w-full flex-shrink-0">
            <HeroBannerSkeleton />
        </div>

        <section className="flex flex-col xl:flex-row gap-6 w-full max-w-[1350px]">
            <div className="flex-1">
                <GuideVideoSkeleton />
            </div>

            <aside className="w-full xl:w-96 flex-none">
                <HospitalTimelineSkeleton />
            </aside>
        </section>
    </div>
);
