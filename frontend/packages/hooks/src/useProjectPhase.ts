/**
 * External dependencies.
 */
import { useFrappeGetDocList } from "frappe-react-sdk";

const DEFAULT_PHASES = [
  "Not Started",
  "Open",
  "Requirement Gathering",
  "Design",
  "Development",
  "UAT",
  "VAPT",
  "Hold",
  "Completed",
  "Maintenance",
  "Cancelled",
];

export const useProjectPhase = () => {
  const { data, error, isLoading } = useFrappeGetDocList<{ name: string }>(
    "Project Phase",
    { fields: ["name"] },
  );

  return {
    phases: data?.map((phase) => phase.name) ?? DEFAULT_PHASES,
    error,
    isLoading,
  };
};
