"use client";

import { Component, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * Error boundary to catch and display errors gracefully
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    // Log to console in development
    if (process.env.NEXT_PUBLIC_DEBUG === "true") {
      console.error("Error Boundary caught:", error);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    // Reload page to reset state
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="container mx-auto max-w-2xl py-10 px-6">
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">
                Something went wrong
              </CardTitle>
              <CardDescription>
                An unexpected error occurred. Please try again.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {process.env.NEXT_PUBLIC_DEBUG === "true" && this.state.error && (
                <div className="bg-destructive/10 border border-destructive/30 rounded p-3 text-sm font-mono">
                  <p className="text-destructive font-bold mb-1">Error Details:</p>
                  <p className="text-muted-foreground break-words">
                    {this.state.error.message}
                  </p>
                </div>
              )}
              <Button onClick={this.handleReset} className="w-full">
                Try Again
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
