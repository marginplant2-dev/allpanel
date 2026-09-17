export type Role = "MOTHER_ADMIN" | "SUPER_ADMIN" | "ADMIN" | "MASTER" | "AGENT" | "USER";

export interface AuthUser {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  status: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
}

export interface ManagedUser {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  parent_id: string | null;
  hierarchy_path: string[];
  status: string;
  credit_limit: number;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
  last_login: string | null;
}

export interface PageMeta {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Paginated<T> {
  items: T[];
  meta: PageMeta;
}

export interface Transaction {
  transaction_id: string;
  from_user_id: string | null;
  to_user_id: string | null;
  amount: number;
  transaction_type: string;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface CreditRequest {
  id: string;
  user_id: string;
  username: string;
  parent_id: string;
  type: "DEPOSIT" | "WITHDRAW";
  amount: number;
  status: "PENDING" | "PROCESSING" | "APPROVED" | "REJECTED";
  note: string | null;
  decision_note: string | null;
  transaction_id: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface AuditLog {
  id: string;
  actor_id: string | null;
  action: string;
  target_id: string | null;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export interface Game {
  id: string;
  name: string;
  slug: string;
  category: string;
  provider: string;
  thumbnail_url: string;
  banner_url?: string;
  status: string;
  featured: boolean;
  sort_order: number;
  tags?: string[];
}

export interface TreeNode {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  status: string;
  parent_id: string | null;
  children: TreeNode[];
}

export interface DashboardStats {
  /** Direct children grouped by role — "my team" on this account's own panel. */
  team_by_role: Partial<Record<Role, number>>;
  total_users: number;
  active_users: number;
  new_users_today: number;
  active_agents: number;
  total_virtual_credits: number;
  credits_transferred_today: number;
  active_events: number;
  active_games: number;
}
