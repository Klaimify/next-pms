/**
 * External dependencies.
 */
import { SolidStages } from "@rtcamp/frappe-ui-react/icons";
import { cva, type VariantProps } from "class-variance-authority";
import { Phase } from "../types";

const stagesIconVariants = cva("size-4 shrink-0", {
  variants: {
    phase: {
      "not-started": "text-ink-gray-4",
      open: "text-ink-blue-3",
      "requirement-gathering": "text-ink-amber-3",
      design: "text-ink-violet-3",
      development: "text-ink-cyan-3",
      uat: "text-ink-amber-3",
      vapt: "text-ink-violet-3",
      hold: "text-ink-gray-4",
      completed: "text-ink-green-3",
      maintenance: "text-ink-gray-6",
      cancelled: "text-ink-red-3",
    } satisfies Record<Phase, string>,
  },
});

export type StagesIconProps = VariantProps<typeof stagesIconVariants>;

export function StagesIcon({ phase }: StagesIconProps) {
  return <SolidStages className={stagesIconVariants({ phase })} />;
}
