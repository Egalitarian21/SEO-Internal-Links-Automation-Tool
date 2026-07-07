import Dashboard from "./pages/Dashboard";
import BlogWorkspace from "./pages/BlogWorkspace";
import ImportPages from "./pages/ImportPages";
import PageLibrary from "./pages/PageLibrary";
import PreviewPage from "./pages/PreviewPage";
import ReviewPage from "./pages/ReviewPage";
import SnapshotPage from "./pages/SnapshotPage";

export default function App() {
  const path = window.location.pathname;
  const parts = path.split("/").filter(Boolean);

  if (path === "/import") return <ImportPages />;
  if (path === "/pages") return <PageLibrary />;
  if (parts[0] === "workspace" && parts[1]) return <BlogWorkspace pageId={parts[1]} />;
  if (parts[0] === "review" && parts[1]) return <ReviewPage pageId={parts[1]} />;
  if (parts[0] === "preview" && parts[1]) return <PreviewPage pageId={parts[1]} />;
  if (parts[0] === "snapshots" && parts[1]) return <SnapshotPage pageId={parts[1]} />;

  return <Dashboard />;
}
