import { NextRequest } from 'next/server';

const backendUrl = () => process.env.BACKEND_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

function passthroughHeaders(headers: Headers): HeadersInit {
  const h: Record<string, string> = {};
  const forward = ['x-api-key', 'content-type'];
  headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (forward.includes(k)) h[k] = value;
  });
  return h;
}

async function getBody(req: NextRequest): Promise<BodyInit | undefined> {
  const ct = req.headers.get('content-type') || '';
  if (ct.includes('multipart/form-data')) {
    const form = await req.formData();
    return form as unknown as BodyInit;
  }
  if (ct.includes('application/json')) {
    const json = await req.json().catch(() => undefined);
    return json ? JSON.stringify(json) : undefined;
  }
  const text = await req.text().catch(() => undefined);
  return text;
}

async function proxy(res: Response) {
  const contentType = res.headers.get('content-type') || '';
  const init: ResponseInit = { status: res.status, headers: { 'content-type': contentType } };
  if (contentType.startsWith('application/json')) {
    const data = await res.json().catch(() => null);
    return Response.json(data, init);
  }
  const buf = await res.arrayBuffer();
  return new Response(buf, init);
}

export async function GET(req: NextRequest, ctx: { params: { path: string[] } }) {
  const target = `${backendUrl()}/${(ctx.params.path || []).join('/')}${req.nextUrl.search || ''}`;
  const res = await fetch(target, { method: 'GET', headers: passthroughHeaders(req.headers), cache: 'no-store' });
  return proxy(res);
}

export async function POST(req: NextRequest, ctx: { params: { path: string[] } }) {
  const target = `${backendUrl()}/${(ctx.params.path || []).join('/')}${req.nextUrl.search || ''}`;
  const body = await getBody(req);
  const res = await fetch(target, { method: 'POST', headers: passthroughHeaders(req.headers), body });
  return proxy(res);
}

export async function PUT(req: NextRequest, ctx: { params: { path: string[] } }) {
  const target = `${backendUrl()}/${(ctx.params.path || []).join('/')}${req.nextUrl.search || ''}`;
  const body = await getBody(req);
  const res = await fetch(target, { method: 'PUT', headers: passthroughHeaders(req.headers), body });
  return proxy(res);
}

export async function DELETE(req: NextRequest, ctx: { params: { path: string[] } }) {
  const target = `${backendUrl()}/${(ctx.params.path || []).join('/')}${req.nextUrl.search || ''}`;
  const res = await fetch(target, { method: 'DELETE', headers: passthroughHeaders(req.headers) });
  return proxy(res);
}


