import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL ?? '';
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ?? '';

export const authIsEnabled = import.meta.env.VITE_ACCESS_REQUIRED === 'true';
export const authConfigured = Boolean(supabaseUrl && supabasePublishableKey);
export const supabase = authConfigured ? createClient(supabaseUrl, supabasePublishableKey) : null;

export async function getAccessToken() {
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  return data.session?.access_token ?? null;
}
