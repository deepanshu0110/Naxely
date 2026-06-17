-- Migration 009: Add Row Level Security policies
-- Enable RLS on ALL tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_reports ENABLE ROW LEVEL SECURITY;

-- users: can only access own row
CREATE POLICY users_own_data ON users
  FOR ALL USING (auth.uid() = id);

-- uploads: can only access own uploads
CREATE POLICY uploads_own_data ON uploads
  FOR ALL USING (auth.uid() = user_id);

-- reports: can only access own reports
CREATE POLICY reports_own_data ON reports
  FOR ALL USING (auth.uid() = user_id);

-- templates: can only access own templates
CREATE POLICY templates_own_data ON templates
  FOR ALL USING (auth.uid() = user_id);

-- workspaces: owner can access all, members can read
CREATE POLICY workspaces_owner ON workspaces
  FOR ALL USING (auth.uid() = owner_id);

-- workspace_members: members can see memberships they belong to
CREATE POLICY workspace_members_access ON workspace_members
  FOR SELECT USING (auth.uid() = user_id);

-- payment_events: users can only see own payment events
CREATE POLICY payment_events_own ON payment_events
  FOR SELECT USING (auth.uid() = user_id);

-- scheduled_reports: users can only access own schedules
CREATE POLICY scheduled_reports_own ON scheduled_reports
  FOR ALL USING (auth.uid() = user_id);