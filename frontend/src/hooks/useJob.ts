/**
 * Hook for polling job status
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api, JobStatus } from '../api/client';

interface UseJobResult {
  status: JobStatus | null;
  isPolling: boolean;
  error: string | null;
  startPolling: (jobId: string) => void;
  stopPolling: () => void;
  reset: () => void;
}

export function useJob(): UseJobResult {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<number | null>(null);
  const jobIdRef = useRef<string | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const poll = useCallback(async () => {
    if (!jobIdRef.current) return;

    try {
      const jobStatus = await api.getJobStatus(jobIdRef.current);
      setStatus(jobStatus);

      // Stop polling when job is complete or errored
      if (jobStatus.status === 'complete' || jobStatus.status === 'error') {
        stopPolling();
        if (jobStatus.status === 'error') {
          setError(jobStatus.error || 'An error occurred');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check job status');
      stopPolling();
    }
  }, [stopPolling]);

  const startPolling = useCallback((jobId: string) => {
    // Stop any existing polling
    stopPolling();

    // Reset state
    setStatus(null);
    setError(null);
    setIsPolling(true);
    jobIdRef.current = jobId;

    // Initial poll
    poll();

    // Start polling interval (every 2 seconds)
    intervalRef.current = window.setInterval(poll, 2000);
  }, [poll, stopPolling]);

  const reset = useCallback(() => {
    stopPolling();
    setStatus(null);
    setError(null);
    jobIdRef.current = null;
  }, [stopPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    status,
    isPolling,
    error,
    startPolling,
    stopPolling,
    reset,
  };
}
