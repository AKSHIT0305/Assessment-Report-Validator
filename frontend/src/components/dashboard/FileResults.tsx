import type {
  ValidationResponse,
  FileValidationResult,
  ValidationIssue,
} from "../../types/validation";

type FileResultsProps = {
  data: ValidationResponse | null;
};

function IssueDetails({
  issue,
}: {
  issue: ValidationIssue;
}) {

  return (
    <li>

      <strong>
        {issue.category}
      </strong>

      {" — "}

      {issue.message}

      {issue.sheet && (
        <span>
          {" | Sheet: "}
          {issue.sheet}
        </span>
      )}

      {issue.cell && (
        <span>
          {" | Cell: "}
          {issue.cell}
        </span>
      )}

      {issue.expected !== undefined && (
        <span>
          {" | Expected: "}
          {String(issue.expected)}
        </span>
      )}

      {issue.actual !== undefined && (
        <span>
          {" | Actual: "}
          {String(issue.actual)}
        </span>
      )}

    </li>
  );
}


function FileCard({
  file,
}: {
  file: FileValidationResult;
}) {

  const isCorrect = file.status === "PASS";
  const isReview = file.status === "REVIEW";

  return (
    <article>

      <h3>
        {isCorrect ? "✅" : isReview ? "⚠️" : "❌"} {file.filename}
      </h3>

      <p>
        Status: {file.status}
      </p>

      {file.template && (
        <p>
          Template: {file.template}
        </p>
      )}

      {file.errors.length > 0 && (
        <div>

          <h4>
            Errors ({file.errors.length})
          </h4>

          <ul>
            {file.errors.map((issue, index) => (
              <IssueDetails
                key={`${issue.code}-${issue.cell}-${index}`}
                issue={issue}
              />
            ))}
          </ul>

        </div>
      )}

      {file.warnings.length > 0 && (
        <div>

          <h4>
            Warnings ({file.warnings.length})
          </h4>

          <ul>
            {file.warnings.map((issue, index) => (
              <IssueDetails
                key={`warning-${issue.code}-${issue.cell}-${index}`}
                issue={issue}
              />
            ))}
          </ul>

        </div>
      )}

      {file.review_items && file.review_items.length > 0 && (
        <div>

          <h4>
            Review Items ({file.review_items.length})
          </h4>

          <ul>
            {file.review_items.map((issue, index) => (
              <IssueDetails
                key={`review-${issue.code}-${issue.cell}-${index}`}
                issue={issue}
              />
            ))}
          </ul>

        </div>
      )}

      {isCorrect && file.errors.length === 0 && (
        <p>
          ✅ No validation errors found.
        </p>
      )}

      {isReview && file.errors.length === 0 && (
        <p>
          ⚠️ Workbook requires manual review but has no errors.
        </p>
      )}

    </article>
  );
}


export default function FileResults({
  data,
}: FileResultsProps) {

  if (!data) {

    return (
      <section>

        <h2>File Results</h2>

        <p>
          Correct files, incorrect files, and review files with
          exact validation errors will appear here.
        </p>

      </section>
    );
  }

  return (
    <section>

      <h2>File Results</h2>

      {/* ================================================
          CORRECT FILES
          ================================================ */}

      <div>

        <h3>
          ✅ Correct Files ({data.correct_files.length})
        </h3>

        {data.correct_files.length === 0 ? (
          <p>
            No files passed validation.
          </p>
        ) : (
          <ul>
            {data.correct_files.map((filename) => (
              <li key={filename}>
                ✅ {filename}
              </li>
            ))}
          </ul>
        )}

      </div>


      {/* ================================================
          INCORRECT FILES
          ================================================ */}

      <div>

        <h3>
          ❌ Incorrect Files ({data.incorrect_files.length})
        </h3>

        {data.incorrect_files.length === 0 ? (
          <p>
            No incorrect files.
          </p>
        ) : (
          <div>
            {data.incorrect_files.map((file) => (
              <FileCard
                key={file.filename}
                file={file}
              />
            ))}
          </div>
        )}

      </div>

      {/* ================================================
          REVIEW FILES
          ================================================ */}

      <div>

        <h3>
          ⚠️ Review Files ({data.review_files?.length || 0})
        </h3>

        {!data.review_files || data.review_files.length === 0 ? (
          <p>
            No files require review.
          </p>
        ) : (
          <div>
            {data.review_files.map((file) => (
              <FileCard
                key={file.filename}
                file={file}
              />
            ))}
          </div>
        )}

      </div>

    </section>
  );
}