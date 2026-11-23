export type Page = 'overview' | 'tb' | 'dr' | 'cases' | 'research' | 'settings';
export type ModelInfo = { task:string; name:string; architecture:string; ready:boolean; model_version:string; dataset:string; message:string|null };
export type ScreeningResult = {
  case_id:string; task:'tb_screening'|'dr_grading'; created_at:string;
  quality:{status:'acceptable'|'poor'|'unsupported';reasons:string[]};
  prediction:{label:string;score:number|null;confidence:number|null};
  uncertainty:{abstain:boolean;reason:string|null};
  explanation:{type:string;overlay_available:boolean;overlay_png_base64?:string;limitations:string};
  provenance:{model_version:string;preprocessing_version:string}; review:{status:string}; processing_ms:number; disclaimer:string;
};
export type CaseSummary = {case_id:string;task:string;created_at:string;quality_status:string;output_label:string;confidence:number|null;abstain:boolean;review_status:string};
