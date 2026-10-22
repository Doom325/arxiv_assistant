import { redirect } from "next/navigation";
import { buildResearchRedirectUrl, executeResearchRedirect } from "../../lib/navigation";

export { buildResearchRedirectUrl, executeResearchRedirect };

export interface ResearchPageProps {
    searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

export default async function ResearchPage({ searchParams }: ResearchPageProps = {}) {
    return executeResearchRedirect(searchParams, redirect);
}
