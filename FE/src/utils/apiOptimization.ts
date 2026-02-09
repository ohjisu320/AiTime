/**
 * API 호출 최적화 유틸리티
 * 
 * 여러 API를 병렬로 호출하여 성능을 개선합니다.
 */

/**
 * 여러 API를 동시에 호출하고 결과를 반환합니다.
 * 
 * @example
 * // 나쁜 예: 순차 호출 (느림)
 * const user = await fetchUser();
 * const posts = await fetchPosts();
 * const comments = await fetchComments();
 * 
 * // 좋은 예: 병렬 호출 (빠름)
 * const [user, posts, comments] = await Promise.all([
 *   fetchUser(),
 *   fetchPosts(),
 *   fetchComments()
 * ]);
 */
export const parallelFetch = async <T extends readonly unknown[]>(
    promises: readonly [...{ [K in keyof T]: Promise<T[K]> }]
): Promise<T> => {
    return Promise.all(promises) as Promise<T>;
};

/**
 * 여러 API를 동시에 호출하되, 일부 실패해도 성공한 것만 반환합니다.
 * 
 * @example
 * const results = await Promise.allSettled([
 *   fetchUser(),
 *   fetchPosts(),
 *   fetchComments()
 * ]);
 * 
 * results.forEach((result, index) => {
 *   if (result.status === 'fulfilled') {
 *     console.log(`API ${index} 성공:`, result.value);
 *   } else {
 *     console.error(`API ${index} 실패:`, result.reason);
 *   }
 * });
 */
export const parallelFetchSettled = async <T extends readonly unknown[]>(
    promises: readonly [...{ [K in keyof T]: Promise<T[K]> }]
): Promise<PromiseSettledResult<T[number]>[]> => {
    return Promise.allSettled(promises);
};

/**
 * 타임아웃을 적용한 API 호출
 * 
 * @example
 * try {
 *   const data = await fetchWithTimeout(fetchUser(), 5000);
 * } catch (error) {
 *   console.error('API 호출 타임아웃 또는 실패');
 * }
 */
export const fetchWithTimeout = <T>(
    promise: Promise<T>,
    timeoutMs: number = 10000
): Promise<T> => {
    return Promise.race([
        promise,
        new Promise<T>((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), timeoutMs)
        ),
    ]);
};

/**
 * 재시도 로직을 포함한 API 호출
 * 
 * @example
 * const data = await fetchWithRetry(
 *   () => fetchUser(),
 *   { maxRetries: 3, retryDelay: 1000 }
 * );
 */
export const fetchWithRetry = async <T>(
    fetchFn: () => Promise<T>,
    options: {
        maxRetries?: number;
        retryDelay?: number;
    } = {}
): Promise<T> => {
    const { maxRetries = 3, retryDelay = 1000 } = options;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await fetchFn();
        } catch (error) {
            if (attempt === maxRetries) {
                throw error;
            }

            console.warn(`API 호출 실패 (시도 ${attempt + 1}/${maxRetries + 1}). ${retryDelay}ms 후 재시도...`);
            await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
    }

    throw new Error('Unexpected error in fetchWithRetry');
};
