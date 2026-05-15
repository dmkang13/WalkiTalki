import { Navigate, Route, Routes } from "react-router-dom";
import { ApiKeyProvider } from "./hooks/useApiKeySession";
import HomePage from "./pages/HomePage";
import BuildPage from "./pages/BuildPage";
import AgentLandingPage from "./pages/AgentLandingPage";
import ChatPage from "./pages/ChatPage";

export default function App() {
  return (
    <ApiKeyProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/build" element={<BuildPage />} />
        <Route path="/agents/:shareSlug" element={<AgentLandingPage />} />
        <Route path="/agents/:shareSlug/chat" element={<ChatPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ApiKeyProvider>
  );
}
