import "@testing-library/jest-dom";
import {
    fireEvent,
    render,
    screen,
    waitFor,
    within,
} from "@testing-library/react";
import AdminPage from "@/app/admin/page";
import {
    getAdminJobStatus,
    getAdminStats,
    triggerGenerateJob,
    triggerScrapeJob,
} from "@/lib/api";

jest.mock("next/link", () => ({
    __esModule: true,
    default: ({ href, children, ...rest }: any) => (
        <a href={href} {...rest}>
            {children}
        </a>
    ),
}));

jest.mock("@/lib/api", () => ({
    getAdminStats: jest.fn(),
    getAdminJobStatus: jest.fn(),
    triggerGenerateJob: jest.fn(),
    triggerScrapeJob: jest.fn(),
}));

const mockGetAdminStats = getAdminStats as jest.MockedFunction<
    typeof getAdminStats
>;
const mockGetAdminJobStatus = getAdminJobStatus as jest.MockedFunction<
    typeof getAdminJobStatus
>;
const mockTriggerGenerateJob = triggerGenerateJob as jest.MockedFunction<
    typeof triggerGenerateJob
>;
const mockTriggerScrapeJob = triggerScrapeJob as jest.MockedFunction<
    typeof triggerScrapeJob
>;

describe("AdminPage provenance panel", () => {
    beforeEach(() => {
        mockGetAdminStats.mockResolvedValue({
            total_headlines: 12,
            real_headlines: 7,
            fake_headlines: 5,
        });

        mockTriggerScrapeJob.mockResolvedValue({
            job_id: "scrape-job-1",
            job_type: "scrape",
            status: "queued",
            requested_count: 1,
            message: "scrape job queued",
            created_at: "2026-04-15T00:00:00+00:00",
            started_at: null,
            finished_at: null,
            error: null,
            result_summary: null,
            result_provenance: null,
        });

        mockTriggerGenerateJob.mockResolvedValue({
            job_id: "gen-job-1",
            job_type: "generate",
            status: "completed",
            requested_count: 1,
            message: "generate job completed",
            created_at: "2026-04-15T00:00:00+00:00",
            started_at: "2026-04-15T00:00:01+00:00",
            finished_at: "2026-04-15T00:00:02+00:00",
            error: null,
            result_summary: "Generated 1 fake headlines (requested 1)",
            result_provenance: {
                schema_version: 1,
                provider: "openai_primary",
                requested_count: 1,
                recent_real_context_count: 1,
                recent_real_context: [
                    {
                        headline_id: 6,
                        text: "Florida man context headline",
                        source_url: "https://example.com/source",
                        created_at: "2026-04-07T16:38:00",
                    },
                ],
            },
        });

        mockGetAdminJobStatus.mockResolvedValue({
            job_id: "gen-job-1",
            job_type: "generate",
            status: "completed",
            requested_count: 1,
            message: "generate job completed",
            created_at: "2026-04-15T00:00:00+00:00",
            started_at: "2026-04-15T00:00:01+00:00",
            finished_at: "2026-04-15T00:00:02+00:00",
            error: null,
            result_summary: "Generated 1 fake headlines (requested 1)",
            result_provenance: {
                schema_version: 1,
                provider: "openai_primary",
                requested_count: 1,
                recent_real_context_count: 1,
                recent_real_context: [
                    {
                        headline_id: 6,
                        text: "Florida man context headline",
                        source_url: "https://example.com/source",
                        created_at: "2026-04-07T16:38:00",
                    },
                ],
            },
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test("renders provenance panel for completed generate job", async () => {
        render(<AdminPage />);

        await waitFor(() => {
            expect(mockGetAdminStats).toHaveBeenCalledTimes(1);
        });

        fireEvent.click(
            screen.getByRole("button", { name: "Trigger Generate" }),
        );

        await waitFor(() => {
            expect(mockTriggerGenerateJob).toHaveBeenCalledWith(1);
        });

        const panel = await screen.findByTestId("job-provenance-panel");
        const scoped = within(panel);

        expect(scoped.getByText("Provenance")).toBeInTheDocument();
        expect(scoped.getByText(/Schema:/)).toHaveTextContent("v1");
        expect(scoped.getByText(/Provider:/)).toHaveTextContent(
            "openai_primary",
        );
        expect(scoped.getByText(/Requested Count:/)).toHaveTextContent("1");
        expect(scoped.getByText(/Context Rows:/)).toHaveTextContent("1");
        expect(
            scoped.getByText("Florida man context headline"),
        ).toBeInTheDocument();

        expect(mockGetAdminJobStatus).not.toHaveBeenCalled();

        const contextItems = scoped.getAllByRole("listitem");
        expect(contextItems).toHaveLength(1);
        expect(contextItems[0]).toHaveTextContent(
            "Florida man context headline",
        );
        expect(contextItems[0]).toHaveTextContent("https://example.com/source");
    });
});
