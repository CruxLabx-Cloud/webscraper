/**
 * Client-side logging utility for monitoring and debugging
 */

export type LogLevel = "debug" | "info" | "warn" | "error";

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  context: string;
  message: string;
  data?: unknown;
}

class Logger {
  private isDev = process.env.NEXT_PUBLIC_DEBUG === "true";
  private logs: LogEntry[] = [];
  private maxLogs = 100;

  debug(context: string, message: string, data?: unknown) {
    this.log("debug", context, message, data);
  }

  info(context: string, message: string, data?: unknown) {
    this.log("info", context, message, data);
  }

  warn(context: string, message: string, data?: unknown) {
    this.log("warn", context, message, data);
  }

  error(context: string, message: string, data?: unknown) {
    this.log("error", context, message, data);
  }

  private log(
    level: LogLevel,
    context: string,
    message: string,
    data?: unknown,
  ) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      context,
      message,
      data,
    };

    // Store logs for debugging
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Log to console in development
    if (this.isDev) {
      const logFn =
        level === "error"
          ? console.error
          : level === "warn"
            ? console.warn
            : level === "info"
              ? console.info
              : console.debug;

      logFn(`[ScrapeFlow:${context}]`, message, data || "");
    }

    // Send to analytics in production
    if (!this.isDev && level === "error") {
      this.reportError(entry);
    }
  }

  private reportError(entry: LogEntry) {
    // Send error to monitoring service (e.g., Sentry)
    // Implement based on your monitoring setup
    try {
      // Example: send to endpoint
      // fetch('/api/logs', { method: 'POST', body: JSON.stringify(entry) })
    } catch {
      // Silently fail to avoid breaking the app
    }
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs() {
    this.logs = [];
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

// Singleton instance
export const logger = new Logger();
