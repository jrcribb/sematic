export type Run = {
  id: string;
  future_state: string;
  name: string;
  calculator_path: string;
  description: string | null;
  tags: Array<string>;
  parent_id: string | null;
  created_at: Date;
  updated_at: Date;
  started_at: Date | null;
  ended_at: Date | null;
  resolved_at: Date | null;
  failed_at: Date | null;
};

export type Artifact = {
  id: string;
  json_summary: any;
  created_at: Date;
  updated_at: Date;
};
