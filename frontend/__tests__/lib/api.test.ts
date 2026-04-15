import {
    getAdminJobStatus,
    getAdminStats,
    getHeadline,
    submitGuess,
    triggerGenerateJob,
} from "@/lib/api";
import {
    beforeAll,
    afterEach,
    describe,
    expect,
    jest,
    test,
} from "@jest/globals";

describe("api client", () => {
    const mockFetch = jest.fn() as jest.MockedFunction<typeof fetch>;

    beforeAll(() => {
        globalThis.fetch = mockFetch;
    });

    afterEach(() => {
        mockFetch.mockReset();
    });

    const mockResponse = (ok: boolean, body: unknown) =>
        ({
            ok,
            json: async () => body,
        }) as unknown as Response;

    test("getHeadline returns parsed response", async () => {
        const mockData = { id: 1, text: "Florida man does a thing" };

        mockFetch.mockResolvedValue(mockResponse(true, mockData));

        await expect(getHeadline()).resolves.toEqual(mockData);
        expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    test("submitGuess throws when response is not ok", async () => {
        mockFetch.mockResolvedValue(mockResponse(false, {}));

        await expect(submitGuess(1, true)).rejects.toThrow(
            "Failed to submit guess",
        );
    });

    test("getAdminStats returns parsed response", async () => {
        const mockData = {
            total_headlines: 5,
            real_headlines: 3,
            fake_headlines: 2,
        };

        mockFetch.mockResolvedValue(mockResponse(true, mockData));

        await expect(getAdminStats()).resolves.toEqual(mockData);
    });

    test("triggerGenerateJob posts count and returns queued job", async () => {
        const queued = {
            job_id: "job-123",
            job_type: "generate",
            status: "queued",
            requested_count: 1,
            message: "generate job queued",
            created_at: "2026-04-08T00:00:00+00:00",
            started_at: null,
            finished_at: null,
            error: null,
            result_summary: null,
            result_provenance: null,
        };

        mockFetch.mockResolvedValue(mockResponse(true, queued));

        await expect(triggerGenerateJob(1)).resolves.toEqual(queued);

        expect(mockFetch).toHaveBeenCalledWith(
            "http://localhost:8000/api/admin/generate",
            expect.objectContaining({
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ count: 1 }),
            }),
        );
    });

    test("getAdminJobStatus throws when response is not ok", async () => {
        mockFetch.mockResolvedValue(mockResponse(false, {}));

        await expect(getAdminJobStatus("job-abc")).rejects.toThrow(
            "Failed to fetch job status",
        );
    });

    test("getAdminJobStatus returns parsed response with provenance", async () => {
        const completed = {
            job_id: "job-999",
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
        };

        mockFetch.mockResolvedValue(mockResponse(true, completed));

        await expect(getAdminJobStatus("job-999")).resolves.toEqual(completed);
        expect(mockFetch).toHaveBeenCalledWith(
            "http://localhost:8000/api/admin/jobs/job-999",
            undefined,
        );
    });
});
