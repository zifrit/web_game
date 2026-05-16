import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ember: "#d66a2f",
        ink: "#101314",
        moss: "#526f55",
        brass: "#b99a57",
        parchment: "#efe5d0",
      },
      boxShadow: {
        panel: "0 18px 60px rgba(16, 19, 20, 0.18)",
      },
    },
  },
  plugins: [],
};

export default config;
