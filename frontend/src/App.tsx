import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WorkstreamBoard } from "./components/WorkstreamBoard";

const queryClient = new QueryClient();

/** Root component: wires the React Query provider around the board. */
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <WorkstreamBoard />
    </QueryClientProvider>
  );
}
