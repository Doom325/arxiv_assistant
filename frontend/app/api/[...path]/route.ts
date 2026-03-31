import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || process.env.INTERNAL_API_URL || "http://backend:8000";

/** Build backend URL, stripping trailing slashes added by Next.js trailingSlash config. */
function buildBackendUrl(path: string[], searchParams: string): string {
    const backendPath = path.filter(Boolean).join("/");
    return `${BACKEND_URL}/${backendPath}${searchParams ? `?${searchParams}` : ""}`;
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
    const { path } = await params;
    const url = buildBackendUrl(path, request.nextUrl.searchParams.toString());

    try {
        const res = await fetch(url, {
            headers: {
                "Content-Type": "application/json",
            },
        });
        const contentType = res.headers.get("Content-Type") || "application/json";

        // Stream binary responses (images, PDFs) as raw bytes
        if (!contentType.startsWith("application/json") && !contentType.startsWith("text/")) {
            const data = await res.arrayBuffer();
            return new NextResponse(data, {
                status: res.status,
                headers: { "Content-Type": contentType },
            });
        }

        const data = await res.text();
        return new NextResponse(data, {
            status: res.status,
            headers: { "Content-Type": contentType },
        });
    } catch (error) {
        console.error(`[API Proxy] GET ${url} failed:`, error);
        return NextResponse.json({ error: "Backend unreachable" }, { status: 502 });
    }
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
    const { path } = await params;
    const url = buildBackendUrl(path, request.nextUrl.searchParams.toString());

    try {
        let body: string | undefined;
        try {
            body = await request.text();
        } catch {
            body = undefined;
        }

        const res = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": request.headers.get("Content-Type") || "application/json",
            },
            body: body || undefined,
        });
        const data = await res.text();
        return new NextResponse(data, {
            status: res.status,
            headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
        });
    } catch (error) {
        console.error(`[API Proxy] POST ${url} failed:`, error);
        return NextResponse.json({ error: "Backend unreachable" }, { status: 502 });
    }
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
    const { path } = await params;
    const url = buildBackendUrl(path, request.nextUrl.searchParams.toString());

    try {
        let body: string | undefined;
        try {
            body = await request.text();
        } catch {
            body = undefined;
        }

        const res = await fetch(url, {
            method: "PATCH",
            headers: {
                "Content-Type": request.headers.get("Content-Type") || "application/json",
            },
            body: body || undefined,
        });
        const data = await res.text();
        return new NextResponse(data, {
            status: res.status,
            headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
        });
    } catch (error) {
        console.error(`[API Proxy] PATCH ${url} failed:`, error);
        return NextResponse.json({ error: "Backend unreachable" }, { status: 502 });
    }
}

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
    const { path } = await params;
    const url = buildBackendUrl(path, request.nextUrl.searchParams.toString());

    try {
        const res = await fetch(url, {
            method: "DELETE",
        });
        const data = await res.text();
        return new NextResponse(data, {
            status: res.status,
            headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" },
        });
    } catch (error) {
        console.error(`[API Proxy] DELETE ${url} failed:`, error);
        return NextResponse.json({ error: "Backend unreachable" }, { status: 502 });
    }
}
