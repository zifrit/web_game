"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Sparkles } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { useSession } from "@/components/providers";
import {
  Button,
  ErrorNotice,
  Field,
  LoadingLine,
  Panel,
  StatBadge,
  formatStatName,
  inputClassName
} from "@/components/ui";
import { api } from "@/lib/api";

const characterSchema = z.object({
  name: z.string().min(3, "Use at least 3 characters.").max(32),
  class_key: z.string().min(1, "Choose a class.")
});

type CharacterValues = z.infer<typeof characterSchema>;

export function CreateCharacterScreen() {
  const { setUser } = useSession();
  const queryClient = useQueryClient();
  const classesQuery = useQuery({
    queryKey: ["character-classes"],
    queryFn: api.characterClasses
  });

  const form = useForm<CharacterValues>({
    resolver: zodResolver(characterSchema),
    defaultValues: {
      name: "",
      class_key: ""
    }
  });

  useEffect(() => {
    const firstClass = classesQuery.data?.[0]?.key;

    if (firstClass && !form.getValues("class_key")) {
      form.setValue("class_key", firstClass, { shouldValidate: true });
    }
  }, [classesQuery.data, form]);

  const mutation = useMutation({
    mutationFn: (values: CharacterValues) =>
      api.createCharacter(values.name, values.class_key),
    onSuccess: async () => {
      const me = await queryClient.fetchQuery({
        queryKey: ["me"],
        queryFn: api.me
      });
      setUser(me);
      await queryClient.invalidateQueries({ queryKey: ["character"] });
    }
  });

  const selectedClass = classesQuery.data?.find(
    (item) => item.key === form.watch("class_key")
  );

  return (
    <main className="rpg-shell min-h-screen px-4 py-8">
      <div className="mx-auto grid w-full max-w-6xl gap-5 lg:grid-cols-[0.85fr_1.15fr]">
        <Panel>
          <div className="mb-6 flex items-center gap-3 text-brass">
            <Sparkles size={24} />
            <div>
              <p className="text-sm font-bold uppercase">First oath</p>
              <h1 className="text-3xl font-black text-parchment">
                Create your hero
              </h1>
            </div>
          </div>

          <form
            className="grid gap-5"
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
          >
            <Field error={form.formState.errors.name?.message} label="Hero name">
              <input
                className={inputClassName}
                placeholder="Arthas"
                {...form.register("name")}
              />
            </Field>

            <Field
              error={form.formState.errors.class_key?.message}
              label="Class"
            >
              <select className={inputClassName} {...form.register("class_key")}>
                {classesQuery.data?.map((characterClass) => (
                  <option key={characterClass.key} value={characterClass.key}>
                    {characterClass.name}
                  </option>
                ))}
              </select>
            </Field>

            <ErrorNotice
              message={
                (mutation.error as Error | null)?.message ??
                (classesQuery.error as Error | null)?.message
              }
            />
            <Button disabled={mutation.isPending || classesQuery.isLoading}>
              {mutation.isPending ? "Forging..." : "Start the campaign"}
            </Button>
          </form>
        </Panel>

        <Panel>
          {classesQuery.isLoading ? (
            <LoadingLine label="Loading character classes" />
          ) : (
            <div className="grid gap-4">
              <div className="grid gap-3 md:grid-cols-2">
                {classesQuery.data?.map((characterClass) => {
                  const selected = characterClass.key === selectedClass?.key;

                  return (
                    <button
                      className={`rounded-lg border p-4 text-left transition ${
                        selected
                          ? "border-brass bg-brass/15"
                          : "border-white/10 bg-white/[0.04] hover:bg-white/[0.08]"
                      }`}
                      key={characterClass.key}
                      onClick={() =>
                        form.setValue("class_key", characterClass.key, {
                          shouldValidate: true
                        })
                      }
                      type="button"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <h2 className="text-xl font-black text-parchment">
                          {characterClass.name}
                        </h2>
                        {selected ? <Check className="text-brass" size={20} /> : null}
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-2">
                        {Object.entries(characterClass.start_stats).map(
                          ([key, value]) => (
                            <StatBadge
                              key={key}
                              label={formatStatName(key)}
                              value={value}
                            />
                          )
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </main>
  );
}
