import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { createUser, type CreateUserPayload } from "@/api/users";
import type { ApiError } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import { toast } from "@/store/toast";
import type { Role } from "@/types";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ROLE_LABELS, creatableRoles } from "@/lib/roles";


export default function CreateUserPage() {
  const navigate = useNavigate();
  const currentUser = useAuthStore((s) => s.user);

  const roles = currentUser ? creatableRoles(currentUser.role) : [];

  const [form, setForm] = useState({
    full_name: "",
    username: "",
    password: "",
    confirm: "",
    role: (roles[0] ?? "USER") as Role,
    credit_limit: 0,
    notes: "",
  });
  const [localError, setLocalError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (payload: CreateUserPayload) => createUser(payload),
    onSuccess: (u) => {
      toast.success("User created", `@${u.username}`);
      navigate("/users");
    },
  });

  const error = localError ?? (mutation.error as ApiError | null)?.message;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setLocalError(null);
    if (form.password !== form.confirm) {
      setLocalError("Passwords do not match");
      return;
    }
    mutation.mutate({
      username: form.username,
      password: form.password,
      full_name: form.full_name,
      role: form.role,
      credit_limit: Number(form.credit_limit) || 0,
      notes: form.notes || null,
    });
  }

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Create User" description="Add a new account to your hierarchy" />
      <Card>
        <CardContent className="pt-6">
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={submit}>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="full_name">Full name</Label>
              <Input id="full_name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="username">Username</Label>
              <Input id="username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="role">Role</Label>
              <Select id="role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as Role })}>
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_LABELS[r]}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <PasswordInput id="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm">Confirm password</Label>
              <PasswordInput id="confirm" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} required />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="credit_limit">Virtual credit limit</Label>
              <Input
                id="credit_limit"
                type="number"
                min={0}
                value={form.credit_limit}
                onChange={(e) => setForm({ ...form, credit_limit: Number(e.target.value) })}
              />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="notes">Notes</Label>
              <Input id="notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>

            {error && <p className="text-sm text-destructive sm:col-span-2">{error}</p>}

            <div className="flex gap-3 sm:col-span-2">
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Creating…" : "Create user"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => navigate("/users")}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
