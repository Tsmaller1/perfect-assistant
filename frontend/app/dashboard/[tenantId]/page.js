"use client";
import Dashboard from "@/components/Dashboard";
export default function DashboardPage({ params }) {
  return <Dashboard tenantId={params.tenantId} />;
}
