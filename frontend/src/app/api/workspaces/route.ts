import { NextResponse } from 'next/server';

let workspaces: any[] = [];

export async function GET() {
  return NextResponse.json({ workspaces });
}

export async function POST(request: Request) {
  try {
    const workspace = await request.json();
    workspace.id = Date.now().toString();
    workspaces.push(workspace);
    return NextResponse.json({ success: true, workspace });
  } catch (error) {
    return NextResponse.json({ error: "Failed to save workspace" }, { status: 400 });
  }
}
