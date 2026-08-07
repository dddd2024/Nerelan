import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { FIXTURE_TASKS } from "@/fixtures/tasks";
import type { PermissionMode, PolicyContract, Task } from "@/types";

export interface CreateTaskInput {
  title: string;
  modelProfileId: string;
  permissionProfile: PermissionMode;
  policy: PolicyContract;
}

/**
 * Return all fixture tasks via react-query.
 * The fixture list remains the Frontend V1 baseline; locally created tasks are
 * inserted into the query cache until the real task API is connected.
 */
export function useTasks() {
  return useQuery<Task[]>({
    queryKey: ["tasks"],
    queryFn: async () => {
      return Promise.resolve(structuredClone(FIXTURE_TASKS) as Task[]);
    },
    staleTime: Infinity,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation<Task, Error, CreateTaskInput>({
    mutationFn: async (input) => {
      const now = new Date().toISOString();
      const task: Task = {
        id: `local-${Date.now()}`,
        title: input.title.trim(),
        issueNumber: 0,
        state: "WAITING_FOR_OWNER",
        riskTier: "R1",
        updatedAt: now,
        nextAction: "等待后端任务执行接口接管",
        permissionProfile: input.permissionProfile,
        modelProfileId: input.modelProfileId,
        branch: "",
        activity: [
          {
            id: `created-${Date.now()}`,
            type: "DISCOVERED",
            timestamp: now,
            title: "任务已创建",
            description: `已绑定模型配置 ${input.modelProfileId}，尚未启动执行器。`,
            expanded: false,
          },
        ],
        changes: [],
        evidence: [],
        authorityStatus: "MISSING",
        testStatus: "PENDING",
        workflowStatus: "UNKNOWN",
      };
      return task;
    },
    onSuccess: (task) => {
      queryClient.setQueryData<Task[]>(["tasks"], (current = []) => [
        task,
        ...current,
      ]);
    },
  });
}
