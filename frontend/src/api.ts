import type { CaseSummary, ModelInfo, ScreeningResult } from './types';

const API = import.meta.env.VITE_API_URL ?? '';
async function request<T>(url:string, init?:RequestInit):Promise<T> {
  const response = await fetch(`${API}${url}`, init);
  if (!response.ok) {
    const body = await response.json().catch(()=>({detail:'Request failed'}));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export const api = {
  health:()=>request<{status:string;models_ready:number;model_count:number}>('/api/health'),
  models:async()=> (await request<{models:ModelInfo[]}>('/api/models')).models,
  cases:(task?:string)=>request<CaseSummary[]>(`/api/cases${task?`?task=${task}`:''}`),
  screen:(task:'tb'|'dr',file:File)=>{const form=new FormData();form.append('file',file);return request<ScreeningResult>(`/api/screen/${task}`,{method:'POST',body:form});},
  detail:(id:string)=>request<Record<string,unknown>>(`/api/cases/${id}`),
  review:(id:string,status:'reviewed'|'indeterminate'|'override',note:string)=>request(`/api/review/${id}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status,note})}),
  remove:(id:string)=>request<void>(`/api/cases/${id}`,{method:'DELETE'}),
  metrics:()=>request<{live_cases_count:number;evaluation_records:unknown[];message:string}>('/api/metrics/summary'),
  report:async(id:string)=>{const response=await fetch(`${API}/api/export/report`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({case_id:id})});if(!response.ok)throw new Error('Report export failed');return response.blob();},
};
