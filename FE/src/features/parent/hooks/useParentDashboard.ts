import { useState, useEffect } from 'react';
import { fetchChildHomeInfo, type ChildHomeResponse } from '../api/dashboardApi';

export const useParentDashboard = () => {
  const [data, setData] = useState<ChildHomeResponse['data'] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      // fetchChildHomeInfo handles errors and returns mock data, so this should almost always succeed
      const response = await fetchChildHomeInfo("child-001");
      setData(response.data);
    } catch (err) {
      console.error("Unexpected error in useParentDashboard", err);
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return {
    data,
    isLoading,
    isError,
    refetch: fetchData,
  };
};