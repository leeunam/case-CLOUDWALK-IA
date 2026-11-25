FROM ruby:3.4-slim@sha256:65680693964528b522a38d85ec5065538c7ab9e75268802aab9770f39ee56de0

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Gemfile Gemfile.lock ./
RUN bundle install

COPY . .
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app \
    && chown -R app:app /app
USER app
EXPOSE 3000
ENTRYPOINT ["/app/bin/docker-entrypoint"]
CMD ["ruby", "bin/rails", "server", "-b", "0.0.0.0", "-P", "/tmp/cloudwalk-server.pid"]
