import { useState } from "react";
import { Link } from "react-router-dom";
import { AuthLayout } from "./AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ForgotPasswordPage() {
  const [submitted, setSubmitted] = useState(false);

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="We'll send reset instructions to your account contact"
      footer={
        <Link to="/login" className="font-medium text-primary hover:underline">
          Back to sign in
        </Link>
      }
    >
      {submitted ? (
        <div className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm">
          If an account matches the details provided, reset instructions will be sent by your
          administrator. Please contact support if you need help.
        </div>
      ) : (
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            setSubmitted(true);
          }}
        >
          <div className="space-y-1.5">
            <Label htmlFor="username">Username</Label>
            <Input id="username" required autoFocus />
          </div>
          <Button type="submit" className="w-full">
            Send reset request
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
