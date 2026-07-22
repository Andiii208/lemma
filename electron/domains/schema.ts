import { z } from 'zod';

const NO_TRAVERSAL = (v: string) => !v.includes('..');

const TransitionSchema = z.object({
  pass: z.string().optional(),
  fail: z.string().optional(),
});

const PhaseSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  order: z.number().int(),
  progress: z.number().min(0).max(100),
  transition: TransitionSchema.optional(),
  handler: z.string().optional(),
});

const RoleSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  emoji: z.string().min(1),
  temperature: z.number().min(0).max(1),
  tools: z.array(z.string()),
});

const AgentSchema = z.object({
  id: z.string().min(1),
  role: z.string().min(1),
    promptPath: z.string().min(1).refine(NO_TRAVERSAL, { message: 'Path traversal not allowed' }),
});

const KnowledgeSchema = z.object({
  path: z.string().min(1).refine(NO_TRAVERSAL, { message: 'Path traversal not allowed' }),
});

const ValidatorSchema = z.object({
  phase: z.string().min(1),
  check: z.string().min(1),
  path: z.string().optional(),
  glob: z.string().optional(),
});

const DirectoriesSchema = z.record(z.string(), z.string());

const DomainConfigRawSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  description: z.string().default(''),
  version: z.string().default('1.0'),
  phases: z.array(PhaseSchema).min(1),
  roles: z.array(RoleSchema).min(1),
  directories: DirectoriesSchema.optional(),
  validators: z.array(ValidatorSchema).optional(),
  agents: z.array(AgentSchema).optional(),
  knowledge: KnowledgeSchema.optional(),
  phase_handlers: z.record(z.string(), z.string()).optional(),
});

export const DomainConfigSchema = DomainConfigRawSchema.superRefine((config, ctx) => {
  const phaseIds = new Set(config.phases.map((p) => p.id));

  for (const phase of config.phases) {
    if (phase.transition?.pass && !phaseIds.has(phase.transition.pass)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `Phase "${phase.id}" transition.pass targets unknown phase "${phase.transition.pass}"`,
        path: ['phases', config.phases.indexOf(phase), 'transition', 'pass'],
      });
    }
    if (phase.transition?.fail && !phaseIds.has(phase.transition.fail)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `Phase "${phase.id}" transition.fail targets unknown phase "${phase.transition.fail}"`,
        path: ['phases', config.phases.indexOf(phase), 'transition', 'fail'],
      });
    }
  }

  const roleIds = new Set(config.roles.map((r) => r.id));
  if (config.agents) {
    for (const agent of config.agents) {
      if (!roleIds.has(agent.role)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Agent "${agent.id}" references unknown role "${agent.role}"`,
          path: ['agents', config.agents.indexOf(agent), 'role'],
        });
      }
    }
  }
});

export type DomainConfig = z.infer<typeof DomainConfigSchema>;
export type Phase = z.infer<typeof PhaseSchema>;
export type Role = z.infer<typeof RoleSchema>;
export type Agent = z.infer<typeof AgentSchema>;
