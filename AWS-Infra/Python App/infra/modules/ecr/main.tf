resource "aws_ecr_repository" "this" {
  name = "${var.name_prefix}-repo"
  image_tag_mutability = "MUTABLE"
  tags = merge(var.tags, { Name = "${var.name_prefix}-repo" })
}
