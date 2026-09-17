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

export interface Wallet {
  user_id: string;
  available_balance: number;
  locked_balance: number;
  updated_at: string;
}

export interface Game {
  id: string;
  name: string;
  slug: string;
  category: string;
  provider: string;
  thumbnail_url: string;
  banner_url?: string;
  status: "active" | "inactive";
  featured: boolean;
  sort_order: number;
  tags?: string[];
}

/** Best price per outcome, carried on list events so the grid can render 1/X/2. */
export interface EventOdds {
  name: string;
  price: number;
  /** Real lay price when the feed is a two-sided exchange; absent on bookmaker feeds. */
  lay?: number | null;
  bookmaker_key: string;
  bookmaker_title: string;
}

export interface SportEvent {
  id: string;
  sport_id: string;
  name: string;
  participants: string[];
  league?: string;
  start_time: string;
  status: "live" | "upcoming" | "finished";
  score?: Record<string, unknown>;
  home_team?: string;
  away_team?: string;
  odds?: EventOdds[];
}

export interface OddsOutcome {
  name: string;
  price: number;
  lay?: number | null;
  status?: string | null;
  size?: string | number | null;
  point?: number;
}

export interface OddsMarket {
  key: string;
  outcomes: OddsOutcome[];
}

export interface Bookmaker {
  key: string;
  title: string;
  last_update?: string;
  /** Feed says the market is not taking bets right now. */
  suspended?: boolean;
  min_stake?: number;
  max_stake?: number;
  markets: OddsMarket[];
}

export interface EventDetail extends SportEvent {
  bookmakers?: Bookmaker[];
}

export type BetStatus = "PENDING" | "WON" | "LOST";

export interface Bet {
  id: string;
  user_id: string;
  event_id: string;
  sport_id: string;
  event_name: string;
  home_team: string;
  away_team: string;
  start_time: string;
  bookmaker_key: string;
  bookmaker_title: string;
  market: string;
  outcome_name: string;
  price: number;
  stake: number;
  potential_payout: number;
  status: BetStatus;
  payout: number | null;
  placed_at: string;
  settled_at: string | null;
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
