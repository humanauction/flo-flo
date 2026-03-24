import { getHeadline, submitGuess } from "@/lib/api";
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
});
