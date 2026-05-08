// Learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";

// Mock environment variables for tests
process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
process.env.NEXT_PUBLIC_DEBUG = "true";
process.env.NEXT_PUBLIC_API_TIMEOUT = "30000";