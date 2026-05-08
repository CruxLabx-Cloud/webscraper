"use client";

import Link from "next/link";
import { Mail, User as UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="container mx-auto max-w-2xl py-10 px-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserIcon className="h-5 w-5" /> Application Settings
          </CardTitle>
          <CardDescription>Configure your experience.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div>
            <p className="font-medium mb-1">Data Storage</p>
            <p className="text-muted-foreground">
              Your watchlist is stored locally in your browser. No account
              required.
            </p>
          </div>
          <div>
            <p className="font-medium mb-1">Notifications</p>
            <p className="text-muted-foreground">
              Enable browser notifications to get alerts when new triggers are
              detected for tracked companies.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if ("Notification" in window) {
                Notification.requestPermission();
              }
            }}
          >
            Enable Notifications
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" /> Watchlist
          </CardTitle>
          <CardDescription>
            Your tracked companies are stored locally and available on the
            Watchlist page.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/watchlist">
            <Button variant="outline" size="sm">
              View Watchlist
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}