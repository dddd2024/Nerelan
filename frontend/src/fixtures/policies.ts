import type { PolicyContract } from "@/types";
import { profileToPolicy, CUSTOM_EXAMPLE_POLICY } from "@/lib/profile-mapper";

export const FIXTURE_POLICIES: PolicyContract[] = [
  profileToPolicy("ASK_FOR_APPROVAL"),
  profileToPolicy("CONTROLLER_REVIEW"),
  profileToPolicy("OWNER_CONTROL"),
  CUSTOM_EXAMPLE_POLICY,
];

export const POLICY_BY_MODE = {
  ASK_FOR_APPROVAL: profileToPolicy("ASK_FOR_APPROVAL"),
  CONTROLLER_REVIEW: profileToPolicy("CONTROLLER_REVIEW"),
  OWNER_CONTROL: profileToPolicy("OWNER_CONTROL"),
  CUSTOM: CUSTOM_EXAMPLE_POLICY,
};

export { CUSTOM_EXAMPLE_POLICY };
