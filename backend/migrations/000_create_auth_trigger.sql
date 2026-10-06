-- NOT APPLIED IN PROD. The "Run in Supabase SQL editor" manual step was
-- never executed (no on_auth_user_created trigger exists in production),
-- and it must stay that way: app/api/deps.py get_current_user is the sole
-- writer of public.users (with ON CONFLICT DO NOTHING covering all unique
-- indexes since NAXELY-BACKEND-8). Applying this trigger would reintroduce
-- a second writer and the exact race it caused. Kept on disk for reference.
-- Run in Supabase SQL editor BEFORE any users sign up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, avatar_url, auth_provider)
  VALUES (
    NEW.id,
    NEW.email,
    -- raw_user_meta_data contains OAuth profile data (name, picture from Google)
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
    COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture'),
    -- raw_app_meta_data contains provider info (NOT app_metadata — that column doesn't exist)
    CASE
      WHEN NEW.raw_app_meta_data->>'provider' = 'google' THEN 'google'
      ELSE 'email'
    END
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();