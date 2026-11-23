import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import App from './App';

beforeEach(()=>{
  vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{
    const url=String(input);
    const body=url.endsWith('/api/models')?{models:[{task:'tb_screening',name:'TB',architecture:'DenseNet',ready:false,model_version:'not-configured',dataset:'Not configured',message:'No checkpoint'},{task:'dr_grading',name:'DR',architecture:'ResNet',ready:false,model_version:'not-configured',dataset:'Not configured',message:'No checkpoint'}]}:
      url.endsWith('/api/cases')?[]:{status:'ok',models_ready:0,model_count:2};
    return {ok:true,status:200,json:async()=>body} as Response;
  }));
});

describe('research dashboard',()=>{
  it('shows safety scope and separate modality workflows',async()=>{
    render(<App/>);
    expect(screen.getByText(/not a diagnosis or a disease-free guarantee/i)).toBeInTheDocument();
    expect(await screen.findByText('TB screening support')).toBeInTheDocument();
    expect(screen.getByText('Diabetic retinopathy')).toBeInTheDocument();
  });
  it('opens the TB workflow explicitly',async()=>{
    render(<App/>);
    fireEvent.click((await screen.findAllByRole('button',{name:/Open workflow/i}))[0]);
    expect(await screen.findByRole('heading',{name:/Upload an image/i})).toBeInTheDocument();
    expect(screen.getByText(/No trained checkpoint is configured/i)).toBeInTheDocument();
  });
});
