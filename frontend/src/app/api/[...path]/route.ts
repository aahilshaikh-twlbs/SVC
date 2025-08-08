import { NextRequest } from 'next/server';

// Hardcoded backend URL since env vars aren't working
const backendUrl = () => 'http://209.38.142.207:8000';

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

type RouteContext = {
  params: Promise<{ path: string[] }>
}

export async function GET(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${(params?.path || []).join('/')}${search}`;
  const res = await fetch(target, { method: 'GET', headers: passthroughHeaders(req.headers), cache: 'no-store' });
  return proxy(res);
}

export async function POST(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${(params?.path || []).join('/')}${search}`;
  const body = await getBody(req);
  const res = await fetch(target, { method: 'POST', headers: passthroughHeaders(req.headers), body });
  return proxy(res);
}

export async function PUT(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${(params?.path || []).join('/')}${search}`;
  const body = await getBody(req);
  const res = await fetch(target, { method: 'PUT', headers: passthroughHeaders(req.headers), body });
  return proxy(res);
}

export async function DELETE(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const search = req.nextUrl.search || '';
  const target = `${backendUrl()}/${(params?.path || []).join('/')}${search}`;
  const res = await fetch(target, { method: 'DELETE', headers: passthroughHeaders(req.headers) });
  return proxy(res);
}


