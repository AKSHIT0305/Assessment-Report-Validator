import type { ValidationResponse } from "../../types/validation";

type ValidationSummaryProps = {
  data: ValidationResponse | null;
};

export default function ValidationSummary({
  data,
}: ValidationSummaryProps) {

  if (!data) {
    return (
      <section>

        <h2>Validation Summary</h2>

        <p>0 / 0 files correct</p>
        <p>Correct: 0</p>
        <p>Incorrect: 0</p>
        <p>Errors: 0</p>

      </section>
    );
  }

  const total = data.total_files;
  const correct = data.summary.correct;
  const incorrect = data.summary.incorrect;

  const totalErrors = data.files.reduce(
    (total, file) => total + file.errors.length,
    0
  );

  return (
    <section>

      <h2>Validation Summary</h2>

      <h3>
        {correct} / {total} files are correct
      </h3>

      <p>
        Correct: {correct}
      </p>

      <p>
        Incorrect: {incorrect}
      </p>

      <p>
        Errors: {totalErrors}
      </p>

      <p>
        Accuracy: {data.summary.percentage_correct}%
      </p>

    </section>
  );
}