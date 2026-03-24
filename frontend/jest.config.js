const nextJest = require("next/jest");

const createJestConfig = nextJest({
    dir: "./",
});

const customJestConfig = {
    testEnvironment: "jest-environment-jsdom",
    moduleNameMapper: {
        "^@/(.*)$": "<rootDir>/src/$1",
    },
    testMatch: ["**/__tests__/**/*.(test|spec).[jt]s?(x)"],
    passWithNoTests: true,
};

module.exports = createJestConfig(customJestConfig);
