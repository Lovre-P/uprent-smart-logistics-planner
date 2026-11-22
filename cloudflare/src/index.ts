import { Container, getContainer } from "@cloudflare/containers";

export class PlannerContainer extends Container {
  defaultPort = 8000;
  sleepAfter = "15m";
}

export default {
  fetch(request: Request, env: { PLANNER: DurableObjectNamespace<PlannerContainer> }) {
    return getContainer(env.PLANNER, "planner").fetch(request);
  },
};
