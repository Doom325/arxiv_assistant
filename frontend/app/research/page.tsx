import { redirect } from "next/navigation";
import { buildResearchRedirectUrl } from "../../lib/navigation";

export { buildResearchRedirectUrl };

export interface ResearchPageProps {
    searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

export default async function ResearchPage({ searchParams }: ResearchPageProps = {}) {
    const resolvedParams = searchParams ? await searchParams : undefined;
    redirect(buildResearchRedirectUrl(resolvedParams));
}
